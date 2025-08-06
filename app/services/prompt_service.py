"""
Prompt service for managing prompts and their usage.

This service provides functionality to manage prompts,
track their usage, and support default prompt handling.

"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ValidationError
from ..models.prompt import Prompt
from .base import BaseService


class PromptService(BaseService):
    """Service for managing prompts and their usage with dependency injection."""

    def __init__(self, db: AsyncSession):
        """
        Initialize prompt service with database session.

        Args:
            db: Database session for prompt operations
        """
        super().__init__(db, "prompt_service")

    async def create_prompt(
        self,
        name: str,
        title: str,
        content: str,
        description: Optional[str] = None,
        is_default: bool = False,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Prompt:
        """Create a new prompt."""
        operation = "create_prompt"
        self._log_operation_start(operation, name=name, is_default=is_default)

        try:
            await self._ensure_db_session()

            # If setting as default, unset any existing defaults
            if is_default:
                await self._bulk_update(Prompt, [], {"is_default": False})

            prompt = Prompt(
                name=name,
                title=title,
                content=content,
                description=description,
                is_default=is_default,
                category=category,
                tags=tags,
            )

            self.db.add(prompt)
            await self.db.commit()
            await self.db.refresh(prompt)

            self._log_operation_success(operation, name=name, prompt_id=str(prompt.id))
            return prompt

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise ValidationError(f"Prompt creation failed: {e}")

    async def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        return await self._get_by_field(Prompt, "name", name)

    async def get_default_prompt(self) -> Optional[Prompt]:
        """Get the default prompt."""
        result = await self.db.execute(select(Prompt).where(Prompt.is_default))
        return result.scalar_one_or_none()

    async def list_prompts(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[List[Prompt], int]:
        """List prompts with optional filtering and pagination."""
        filters = []

        if active_only:
            filters.append(Prompt.is_active)
        if category:
            filters.append(Prompt.category == category)

        if search:
            # Use the base service search functionality
            return await self._search_entities(
                model=Prompt,
                search_fields=["name", "title", "content", "tags"],
                search_term=search,
                additional_filters=filters,
                page=page,
                size=size,
            )
        else:
            return await self._list_with_filters(
                model=Prompt,
                filters=filters,
                page=page,
                size=size,
                order_by=Prompt.name,
            )

    async def update_prompt(self, name: str, updates: dict) -> Optional[Prompt]:
        """Update a prompt."""
        operation = "update_prompt"
        self._log_operation_start(operation, name=name, updates=list(updates.keys()))

        try:
            prompt = await self.get_prompt(name)

            # Handle is_default specially
            if updates.get("is_default"):
                # Unset any existing defaults
                await self._bulk_update(Prompt, [], {"is_default": False})

            # Update other fields
            prompt = await self._update_entity(prompt, updates)

            self._log_operation_success(operation, name=name, prompt_id=str(prompt.id))
            print("ASDFASDFASDFASDFASDFASDFASDF", prompt)
            return prompt

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise ValidationError(f"Prompt update failed: {e}")

    async def delete_prompt(self, name: str) -> bool:
        """Delete a prompt and ensure a default remains."""
        operation = "delete_prompt"
        self._log_operation_start(operation, name=name)

        try:
            prompt = await self.get_prompt(name)

            was_default = prompt.is_default
            await self._delete_entity(prompt)

            # If we deleted the default prompt, assign a new default
            if was_default:
                await self._ensure_default_prompt()

            self._log_operation_success(operation, name=name)
            return True

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def set_default_prompt(self, name: str) -> bool:
        """Set a prompt as the default."""
        operation = "set_default_prompt"
        self._log_operation_start(operation, name=name)

        try:
            # First unset all defaults
            await self._bulk_update(Prompt, [], {"is_default": False})

            # Set the new default
            result = await self._bulk_update(
                Prompt, [Prompt.name == name], {"is_default": True}
            )

            if result > 0:
                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def activate_prompt(self, name: str) -> bool:
        """Activate a prompt."""
        operation = "activate_prompt"
        self._log_operation_start(operation, name=name)

        try:
            result = await self._bulk_update(
                Prompt, [Prompt.name == name], {"is_active": True}
            )

            if result > 0:
                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def deactivate_prompt(self, name: str) -> bool:
        """Deactivate a prompt and ensure a default remains."""
        operation = "deactivate_prompt"
        self._log_operation_start(operation, name=name)

        try:
            # Get the prompt to check if it's the default
            prompt = await self.get_prompt(name)

            was_default = prompt.is_default

            result = await self._bulk_update(
                Prompt, [Prompt.name == name], {"is_active": False}
            )

            if result > 0:
                # If we deactivated the default prompt, assign a new default
                if was_default:
                    await self._ensure_default_prompt()

                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def record_prompt_usage(self, name: str) -> bool:
        """Record a prompt usage event."""
        try:
            prompt = await self.get_prompt(name)

            prompt.record_usage()
            await self.db.commit()
            return True

        except Exception as e:
            self.logger.warning(f"Failed to record prompt usage: {e}")
            await self.db.rollback()
            return False

    async def get_categories(self) -> List[str]:
        """Get all available prompt categories."""
        result = await self.db.execute(
            select(Prompt.category)
            .where(Prompt.category.isnot(None))
            .distinct()
            .order_by(Prompt.category)
        )
        return [row[0] for row in result.all()]

    async def get_all_tags(self) -> List[str]:
        """Get all available tags."""
        result = await self.db.execute(
            select(Prompt.tags).where(Prompt.tags.isnot(None))
        )
        all_tags = set()
        for row in result.all():
            if row[0]:
                all_tags.update(row[0])
        return sorted(all_tags)

    async def get_prompt_stats(self) -> Dict[str, Any]:
        """Get prompt usage statistics."""
        # Total counts
        total_prompts = await self.db.scalar(select(func.count(Prompt.id)))
        active_prompts = await self.db.scalar(
            select(func.count(Prompt.id)).where(Prompt.is_active)
        )

        # Most used prompts
        most_used = await self.db.execute(
            select(Prompt).order_by(Prompt.usage_count.desc()).limit(5)
        )
        most_used_list = [
            {
                "name": p.name,
                "title": p.title,
                "usage_count": p.usage_count,
                "last_used_at": p.last_used_at,
            }
            for p in most_used.scalars().all()
        ]

        # Recently used prompts
        recently_used = await self.db.execute(
            select(Prompt)
            .where(Prompt.last_used_at.isnot(None))
            .order_by(Prompt.last_used_at.desc())
            .limit(5)
        )
        recently_used_list = [
            {
                "name": p.name,
                "title": p.title,
                "usage_count": p.usage_count,
                "last_used_at": p.last_used_at,
            }
            for p in recently_used.scalars().all()
        ]

        # Default prompt
        default_prompt = await self.get_default_prompt()

        return {
            "total_prompts": total_prompts,
            "active_prompts": active_prompts,
            "default_prompt": default_prompt.name if default_prompt else None,
            "most_used": most_used_list,
            "recently_used": recently_used_list,
            "categories": await self.get_categories(),
            "total_tags": len(await self.get_all_tags()),
        }

    async def _ensure_default_prompt(self) -> bool:
        """Ensure there is at least one default prompt active."""
        operation = "ensure_default_prompt"
        self._log_operation_start(operation)

        try:
            # Check if there's any active default prompt
            default_prompt = await self.db.execute(
                select(Prompt).where(and_(Prompt.is_default, Prompt.is_active))
            )
            default_prompt = default_prompt.scalar_one_or_none()

            if default_prompt:
                return True  # Already have a default

            # Find the most recently used active prompt to make default
            candidate = await self.db.execute(
                select(Prompt)
                .where(Prompt.is_active)
                .order_by(Prompt.usage_count.desc(), Prompt.created_at.desc())
                .limit(1)
            )
            candidate = candidate.scalar_one_or_none()

            if candidate:
                candidate.is_default = True
                await self.db.commit()
                self._log_operation_success(operation, new_default=candidate.name)
                return True
            else:
                self.logger.warning("No active prompts available to set as default")
                return False

        except Exception as e:
            self._log_operation_error(operation, e)
            await self.db.rollback()
            return False
