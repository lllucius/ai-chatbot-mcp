"""
LLM Profile service for managing LLM parameter configurations.

This service provides functionality to manage LLM parameter profiles,
track their usage, and support default profile handling.

"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, ValidationError
from ..models.llm_profile import LLMProfile
from ..schemas.llm_profile import (LLMProfileCreate)
from .base import BaseService


class LLMProfileService(BaseService):
    """Service for managing LLM parameter profiles and their usage with dependency injection."""

    def __init__(self, db: AsyncSession):
        """
        Initialize LLM profile service with database session.

        Args:
            db: Database session for LLM profile operations
        """
        super().__init__(db, "llm_profile_service")

    async def create_profile(self, request: LLMProfileCreate) -> LLMProfile:
        """Create a new LLM profile."""
        operation = "create_profile"
        self._log_operation_start(operation, name=request.name, is_default=request.is_default)
        try:
            await self._ensure_db_session()
            profile = LLMProfile(
                name=request.name,
                title=request.title,
                model_name=request.model_name,
                description=request.description,
                is_default=request.is_default,
                **request.parameters,
            )

            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)

            self._log_operation_success(operation, name=request.name, profile_id=str(profile.id))
            return profile

        except Exception as e:
            self._log_operation_error(operation, e, name=request.name)
            await self.db.rollback()
            raise ValidationError(f"LLM profile creation failed: {e}")

    async def get_profile(self, name: str) -> Optional[LLMProfile]:
        """Get a profile by name."""
        try:
            return await self._get_by_field(LLMProfile, "name", name)
        except NotFoundError:
            return None

    async def get_default_profile(self) -> Optional[LLMProfile]:
        """Get the default profile."""
        result = await self.db.execute(select(LLMProfile).where(LLMProfile.is_default))
        return result.scalar_one_or_none()

    async def list_profiles(
        self,
        active_only: bool = True,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[List[LLMProfile], int]:
        """List profiles with optional filtering and pagination."""
        filters = []

        if active_only:
            filters.append(LLMProfile.is_active)

        if search:
            # Use the base service search functionality
            return await self._search_entities(
                model=LLMProfile,
                search_fields=["name", "title", "description"],
                search_term=search,
                additional_filters=filters,
                page=page,
                size=size,
            )
        else:
            return await self._list_with_filters(
                model=LLMProfile,
                filters=filters,
                page=page,
                size=size,
                order_by=LLMProfile.name,
            )

    async def update_profile(self, name: str, **updates) -> Optional[LLMProfile]:
        """Update a profile."""
        operation = "update_profile"
        self._log_operation_start(operation, name=name, updates=list(updates.keys()))

        try:
            profile = await self.get_profile(name)
            if not profile:
                return None

            # Handle is_default specially
            if updates.get("is_default"):
                # Unset any existing defaults
                await self._bulk_update(LLMProfile, [], {"is_default": False})

            # Update fields
            profile = await self._update_entity(profile, updates)

            self._log_operation_success(operation, name=name, profile_id=str(profile.id))
            return profile

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise ValidationError(f"LLM profile update failed: {e}")

    async def delete_profile(self, name: str) -> bool:
        """Delete a profile and ensure a default remains."""
        operation = "delete_profile"
        self._log_operation_start(operation, name=name)

        try:
            profile = await self.get_profile(name)
            if not profile:
                return False

            was_default = profile.is_default
            await self._delete_entity(profile)

            # If we deleted the default profile, assign a new default
            if was_default:
                await self._ensure_default_profile()

            self._log_operation_success(operation, name=name)
            return True

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def set_default_profile(self, name: str) -> bool:
        """Set a profile as the default."""
        operation = "set_default_profile"
        self._log_operation_start(operation, name=name)

        try:
            # First unset all defaults
            await self._bulk_update(LLMProfile, [], {"is_default": False})

            # Set the new default
            result = await self._bulk_update(
                LLMProfile, [LLMProfile.name == name], {"is_default": True}
            )

            if result > 0:
                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def activate_profile(self, name: str) -> bool:
        """Activate a profile."""
        operation = "activate_profile"
        self._log_operation_start(operation, name=name)

        try:
            result = await self._bulk_update(
                LLMProfile, [LLMProfile.name == name], {"is_active": True}
            )

            if result > 0:
                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def deactivate_profile(self, name: str) -> bool:
        """Deactivate a profile and ensure a default remains."""
        operation = "deactivate_profile"
        self._log_operation_start(operation, name=name)

        try:
            # Get the profile to check if it's the default
            profile = await self.get_profile(name)
            if not profile:
                return False

            was_default = profile.is_default

            result = await self._bulk_update(
                LLMProfile, [LLMProfile.name == name], {"is_active": False}
            )

            if result > 0:
                # If we deactivated the default profile, assign a new default
                if was_default:
                    await self._ensure_default_profile()

                self._log_operation_success(operation, name=name)
                return True
            return False

        except Exception as e:
            self._log_operation_error(operation, e, name=name)
            await self.db.rollback()
            raise

    async def record_profile_usage(self, name: str) -> bool:
        """Record a profile usage event."""
        try:
            profile = await self.get_profile(name)
            if not profile:
                return False

            profile.record_usage()
            await self.db.commit()
            return True

        except Exception as e:
            self.logger.warning(f"Failed to record profile usage: {e}")
            await self.db.rollback()
            return False

    async def get_profile_for_openai(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get profile parameters formatted for OpenAI API."""
        if name:
            profile = await self.get_profile(name)
        else:
            profile = await self.get_default_profile()

        if not profile:
            return {}

        # Record usage
        await self.record_profile_usage(profile.name)

        return profile.to_openai_params()

    async def clone_profile(
        self, source_name: str, new_name: str, new_title: Optional[str] = None
    ) -> Optional[LLMProfile]:
        """Clone an existing profile with a new name."""
        operation = "clone_profile"
        self._log_operation_start(operation, source_name=source_name, new_name=new_name)

        try:
            source_profile = await self.get_profile(source_name)
            if not source_profile:
                return None

            new_profile = await self.create_profile(
                name=new_name,
                title=new_title or f"{source_profile.title} (Copy)",
                description=source_profile.description,
                is_default=False,  # Never clone as default
                temperature=source_profile.temperature,
                top_p=source_profile.top_p,
                top_k=source_profile.top_k,
                repeat_penalty=source_profile.repeat_penalty,
                max_tokens=source_profile.max_tokens,
                max_new_tokens=source_profile.max_new_tokens,
                context_length=source_profile.context_length,
                presence_penalty=source_profile.presence_penalty,
                frequency_penalty=source_profile.frequency_penalty,
                stop=source_profile.stop,
                other_params=source_profile.other_params,
            )

            self._log_operation_success(operation, source_name=source_name, new_name=new_name)
            return new_profile

        except Exception as e:
            self._log_operation_error(operation, e, source_name=source_name, new_name=new_name)
            raise

    async def get_profile_stats(self) -> Dict[str, Any]:
        """Get profile usage statistics."""
        # Total counts
        total_profiles = await self.db.scalar(select(func.count(LLMProfile.id)))
        active_profiles = await self.db.scalar(
            select(func.count(LLMProfile.id)).where(LLMProfile.is_active)
        )

        # Most used profiles
        most_used = await self.db.execute(
            select(LLMProfile).order_by(LLMProfile.usage_count.desc()).limit(5)
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

        # Recently used profiles
        recently_used = await self.db.execute(
            select(LLMProfile)
            .where(LLMProfile.last_used_at.isnot(None))
            .order_by(LLMProfile.last_used_at.desc())
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

        # Default profile
        default_profile = await self.get_default_profile()

        return {
            "total_profiles": total_profiles,
            "active_profiles": active_profiles,
            "inactive_profiles": total_profiles - active_profiles,
            "default_profile": default_profile.name if default_profile else None,
            "most_used": most_used_list,
            "recently_used": recently_used_list,
        }

    async def validate_parameters(self, **parameters) -> Dict[str, str]:
        """Validate LLM parameters and return any errors."""
        errors = {}

        if "temperature" in parameters:
            temp = parameters["temperature"]
            if temp is not None and (temp < 0.0 or temp > 2.0):
                errors["temperature"] = "Temperature must be between 0.0 and 2.0"

        if "top_p" in parameters:
            top_p = parameters["top_p"]
            if top_p is not None and (top_p < 0.0 or top_p > 1.0):
                errors["top_p"] = "top_p must be between 0.0 and 1.0"

        if "top_k" in parameters:
            top_k = parameters["top_k"]
            if top_k is not None and top_k <= 0:
                errors["top_k"] = "top_k must be a positive integer"

        if "repeat_penalty" in parameters:
            repeat_penalty = parameters["repeat_penalty"]
            if repeat_penalty is not None and repeat_penalty <= 0:
                errors["repeat_penalty"] = "repeat_penalty must be positive"

        if "max_tokens" in parameters:
            max_tokens = parameters["max_tokens"]
            if max_tokens is not None and max_tokens <= 0:
                errors["max_tokens"] = "max_tokens must be positive"

        if "max_new_tokens" in parameters:
            max_new_tokens = parameters["max_new_tokens"]
            if max_new_tokens is not None and max_new_tokens <= 0:
                errors["max_new_tokens"] = "max_new_tokens must be positive"

        if "context_length" in parameters:
            context_length = parameters["context_length"]
            if context_length is not None and context_length <= 0:
                errors["context_length"] = "context_length must be positive"

        if "presence_penalty" in parameters:
            presence_penalty = parameters["presence_penalty"]
            if presence_penalty is not None and (presence_penalty < -2.0 or presence_penalty > 2.0):
                errors["presence_penalty"] = "presence_penalty must be between -2.0 and 2.0"

        if "frequency_penalty" in parameters:
            frequency_penalty = parameters["frequency_penalty"]
            if frequency_penalty is not None and (
                frequency_penalty < -2.0 or frequency_penalty > 2.0
            ):
                errors["frequency_penalty"] = "frequency_penalty must be between -2.0 and 2.0"

        return errors

    async def _ensure_default_profile(self) -> bool:
        """Ensure there is at least one default LLM profile active."""
        operation = "ensure_default_profile"
        self._log_operation_start(operation)

        try:
            # Check if there's any active default profile
            default_profile = await self.db.execute(
                select(LLMProfile).where(and_(LLMProfile.is_default, LLMProfile.is_active))
            )
            default_profile = default_profile.scalar_one_or_none()

            if default_profile:
                return True  # Already have a default

            # Find the most recently used active profile to make default
            candidate = await self.db.execute(
                select(LLMProfile)
                .where(LLMProfile.is_active)
                .order_by(LLMProfile.usage_count.desc(), LLMProfile.created_at.desc())
                .limit(1)
            )
            candidate = candidate.scalar_one_or_none()

            if candidate:
                candidate.is_default = True
                await self.db.commit()
                self._log_operation_success(operation, new_default=candidate.name)
                return True
            else:
                self.logger.warning("No active LLM profiles available to set as default")
                return False

        except Exception as e:
            self._log_operation_error(operation, e)
            await self.db.rollback()
            return False
