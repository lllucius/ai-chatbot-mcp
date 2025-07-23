"""
Prompt service for managing prompts and their usage.

This service provides functionality to manage prompts,
track their usage, and support default prompt handling.

Current Date and Time (UTC): 2025-07-23 03:30:00
Current User: lllucius / assistant
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.prompt import Prompt
from ..database import AsyncSessionLocal
from ..utils.logging import get_api_logger

logger = get_api_logger("prompt_service")


class PromptService:
    """Service for managing prompts and their usage."""

    @staticmethod
    async def create_prompt(
        name: str,
        title: str,
        content: str,
        description: Optional[str] = None,
        is_default: bool = False,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Prompt:
        """Create a new prompt."""
        async with AsyncSessionLocal() as db:
            # If setting as default, unset any existing defaults
            if is_default:
                await db.execute(
                    update(Prompt).values(is_default=False)
                )
            
            prompt = Prompt(
                name=name,
                title=title,
                content=content,
                description=description,
                is_default=is_default,
                category=category
            )
            
            if tags:
                prompt.tag_list = tags
            
            db.add(prompt)
            await db.commit()
            await db.refresh(prompt)
            
            logger.info(f"Created prompt: {name}")
            return prompt

    @staticmethod
    async def get_prompt(name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Prompt).where(Prompt.name == name)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_default_prompt() -> Optional[Prompt]:
        """Get the default prompt."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Prompt).where(Prompt.is_default == True)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def list_prompts(
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Prompt]:
        """List prompts with optional filtering."""
        async with AsyncSessionLocal() as db:
            query = select(Prompt)
            
            filters = []
            if active_only:
                filters.append(Prompt.is_active == True)
            if category:
                filters.append(Prompt.category == category)
            if search:
                # Search in name, title, content, and tags
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        Prompt.name.ilike(search_term),
                        Prompt.title.ilike(search_term),
                        Prompt.content.ilike(search_term),
                        Prompt.tags.ilike(search_term)
                    )
                )
                
            if filters:
                query = query.where(and_(*filters))
                
            result = await db.execute(query.order_by(Prompt.name))
            return list(result.scalars().all())

    @staticmethod
    async def update_prompt(
        name: str,
        **updates
    ) -> Optional[Prompt]:
        """Update a prompt."""
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(
                select(Prompt).where(Prompt.name == name)
            )
            prompt = prompt.scalar_one_or_none()
            
            if not prompt:
                return None
            
            # Handle is_default specially
            if updates.get("is_default"):
                # Unset any existing defaults
                await db.execute(
                    update(Prompt).values(is_default=False)
                )
            
            # Handle tags list conversion
            if "tags" in updates and isinstance(updates["tags"], list):
                prompt.tag_list = updates.pop("tags")
                
            for key, value in updates.items():
                if hasattr(prompt, key):
                    setattr(prompt, key, value)
                    
            await db.commit()
            await db.refresh(prompt)
            
            logger.info(f"Updated prompt: {name}")
            return prompt

    @staticmethod
    async def delete_prompt(name: str) -> bool:
        """Delete a prompt."""
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(
                select(Prompt).where(Prompt.name == name)
            )
            prompt = prompt.scalar_one_or_none()
            
            if not prompt:
                return False
                
            await db.delete(prompt)
            await db.commit()
            
            logger.info(f"Deleted prompt: {name}")
            return True

    @staticmethod
    async def set_default_prompt(name: str) -> bool:
        """Set a prompt as the default."""
        async with AsyncSessionLocal() as db:
            # First unset all defaults
            await db.execute(
                update(Prompt).values(is_default=False)
            )
            
            # Set the new default
            result = await db.execute(
                update(Prompt)
                .where(Prompt.name == name)
                .values(is_default=True)
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Set default prompt: {name}")
                return True
            return False

    @staticmethod
    async def activate_prompt(name: str) -> bool:
        """Activate a prompt."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(Prompt)
                .where(Prompt.name == name)
                .values(is_active=True)
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Activated prompt: {name}")
                return True
            return False

    @staticmethod
    async def deactivate_prompt(name: str) -> bool:
        """Deactivate a prompt."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(Prompt)
                .where(Prompt.name == name)
                .values(is_active=False)
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Deactivated prompt: {name}")
                return True
            return False

    @staticmethod
    async def record_prompt_usage(name: str) -> bool:
        """Record a prompt usage event."""
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(
                select(Prompt).where(Prompt.name == name)
            )
            prompt = prompt.scalar_one_or_none()
            
            if not prompt:
                return False
                
            prompt.record_usage()
            await db.commit()
            
            return True

    @staticmethod
    async def get_categories() -> List[str]:
        """Get all available prompt categories."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Prompt.category)
                .where(Prompt.category.isnot(None))
                .distinct()
                .order_by(Prompt.category)
            )
            return [row[0] for row in result.all()]

    @staticmethod
    async def get_all_tags() -> List[str]:
        """Get all available tags."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Prompt.tags)
                .where(Prompt.tags.isnot(None))
            )
            all_tags = set()
            for row in result.all():
                if row[0]:
                    tags = [tag.strip() for tag in row[0].split(",") if tag.strip()]
                    all_tags.update(tags)
            return sorted(list(all_tags))

    @staticmethod
    async def get_prompt_stats() -> Dict[str, Any]:
        """Get prompt usage statistics."""
        async with AsyncSessionLocal() as db:
            # Total counts
            total_prompts = await db.scalar(select(func.count(Prompt.id)))
            active_prompts = await db.scalar(
                select(func.count(Prompt.id)).where(Prompt.is_active == True)
            )
            
            # Most used prompts
            most_used = await db.execute(
                select(Prompt)
                .order_by(Prompt.usage_count.desc())
                .limit(5)
            )
            most_used_list = [
                {
                    "name": p.name,
                    "title": p.title,
                    "usage_count": p.usage_count,
                    "last_used_at": p.last_used_at
                }
                for p in most_used.scalars().all()
            ]
            
            # Recently used prompts
            recently_used = await db.execute(
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
                    "last_used_at": p.last_used_at
                }
                for p in recently_used.scalars().all()
            ]
            
            # Default prompt
            default_prompt = await PromptService.get_default_prompt()
            
            return {
                "total_prompts": total_prompts,
                "active_prompts": active_prompts,
                "inactive_prompts": total_prompts - active_prompts,
                "default_prompt": default_prompt.name if default_prompt else None,
                "most_used": most_used_list,
                "recently_used": recently_used_list,
                "categories": await PromptService.get_categories(),
                "total_tags": len(await PromptService.get_all_tags())
            }