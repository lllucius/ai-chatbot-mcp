"""
LLM Profile service for managing LLM parameter configurations.

This service provides functionality to manage LLM parameter profiles,
track their usage, and support default profile handling.

Current Date and Time (UTC): 2025-07-23 03:30:00
Current User: lllucius / assistant
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select, update

from ..database import AsyncSessionLocal
from ..models.llm_profile import LLMProfile
from ..utils.logging import get_api_logger

logger = get_api_logger("llm_profile_service")


class LLMProfileService:
    """Service for managing LLM parameter profiles and their usage."""

    @staticmethod
    async def create_profile(
        name: str,
        title: str,
        description: Optional[str] = None,
        is_default: bool = False,
        **parameters,
    ) -> LLMProfile:
        """Create a new LLM profile."""
        async with AsyncSessionLocal() as db:
            # If setting as default, unset any existing defaults
            if is_default:
                await db.execute(update(LLMProfile).values(is_default=False))

            # Separate known parameters from others
            known_params = {
                "temperature",
                "top_p",
                "top_k",
                "repeat_penalty",
                "max_tokens",
                "max_new_tokens",
                "context_length",
                "presence_penalty",
                "frequency_penalty",
                "stop",
            }

            profile_params = {}
            other_params = {}

            for key, value in parameters.items():
                if key in known_params:
                    profile_params[key] = value
                else:
                    other_params[key] = value

            profile = LLMProfile(
                name=name,
                title=title,
                description=description,
                is_default=is_default,
                other_params=other_params if other_params else None,
                **profile_params,
            )

            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            logger.info(f"Created LLM profile: {name}")
            return profile

    @staticmethod
    async def get_profile(name: str) -> Optional[LLMProfile]:
        """Get a profile by name."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(LLMProfile).where(LLMProfile.name == name))
            return result.scalar_one_or_none()

    @staticmethod
    async def get_default_profile() -> Optional[LLMProfile]:
        """Get the default profile."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(LLMProfile).where(LLMProfile.is_default == True)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def list_profiles(
        active_only: bool = True, search: Optional[str] = None
    ) -> List[LLMProfile]:
        """List profiles with optional filtering."""
        async with AsyncSessionLocal() as db:
            query = select(LLMProfile)

            filters = []
            if active_only:
                filters.append(LLMProfile.is_active == True)
            if search:
                # Search in name, title, and description
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        LLMProfile.name.ilike(search_term),
                        LLMProfile.title.ilike(search_term),
                        LLMProfile.description.ilike(search_term),
                    )
                )

            if filters:
                query = query.where(and_(*filters))

            result = await db.execute(query.order_by(LLMProfile.name))
            return list(result.scalars().all())

    @staticmethod
    async def update_profile(name: str, **updates) -> Optional[LLMProfile]:
        """Update a profile."""
        async with AsyncSessionLocal() as db:
            profile = await db.execute(
                select(LLMProfile).where(LLMProfile.name == name)
            )
            profile = profile.scalar_one_or_none()

            if not profile:
                return None

            # Handle is_default specially
            if updates.get("is_default"):
                # Unset any existing defaults
                await db.execute(update(LLMProfile).values(is_default=False))

            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            await db.commit()
            await db.refresh(profile)

            logger.info(f"Updated LLM profile: {name}")
            return profile

    @staticmethod
    async def delete_profile(name: str) -> bool:
        """Delete a profile and ensure a default remains."""
        async with AsyncSessionLocal() as db:
            profile = await db.execute(
                select(LLMProfile).where(LLMProfile.name == name)
            )
            profile = profile.scalar_one_or_none()

            if not profile:
                return False

            was_default = profile.is_default

            await db.delete(profile)
            await db.commit()

            # If we deleted the default profile, assign a new default
            if was_default:
                await LLMProfileService._ensure_default_profile()

            logger.info(f"Deleted LLM profile: {name}")
            return True

    @staticmethod
    async def set_default_profile(name: str) -> bool:
        """Set a profile as the default."""
        async with AsyncSessionLocal() as db:
            # First unset all defaults
            await db.execute(update(LLMProfile).values(is_default=False))

            # Set the new default
            result = await db.execute(
                update(LLMProfile)
                .where(LLMProfile.name == name)
                .values(is_default=True)
            )
            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Set default LLM profile: {name}")
                return True
            return False

    @staticmethod
    async def activate_profile(name: str) -> bool:
        """Activate a profile."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(LLMProfile).where(LLMProfile.name == name).values(is_active=True)
            )
            await db.commit()

            if result.rowcount > 0:
                logger.info(f"Activated LLM profile: {name}")
                return True
            return False

    @staticmethod
    async def deactivate_profile(name: str) -> bool:
        """Deactivate a profile and ensure a default remains."""
        async with AsyncSessionLocal() as db:
            # Get the profile to check if it's the default
            profile = await db.execute(
                select(LLMProfile).where(LLMProfile.name == name)
            )
            profile = profile.scalar_one_or_none()

            if not profile:
                return False

            was_default = profile.is_default

            result = await db.execute(
                update(LLMProfile)
                .where(LLMProfile.name == name)
                .values(is_active=False)
            )
            await db.commit()

            if result.rowcount > 0:
                # If we deactivated the default profile, assign a new default
                if was_default:
                    await LLMProfileService._ensure_default_profile()

                logger.info(f"Deactivated LLM profile: {name}")
                return True
            return False

    @staticmethod
    async def record_profile_usage(name: str) -> bool:
        """Record a profile usage event."""
        async with AsyncSessionLocal() as db:
            profile = await db.execute(
                select(LLMProfile).where(LLMProfile.name == name)
            )
            profile = profile.scalar_one_or_none()

            if not profile:
                return False

            profile.record_usage()
            await db.commit()

            return True

    @staticmethod
    async def get_profile_for_openai(name: Optional[str] = None) -> Dict[str, Any]:
        """Get profile parameters formatted for OpenAI API."""
        if name:
            profile = await LLMProfileService.get_profile(name)
        else:
            profile = await LLMProfileService.get_default_profile()

        if not profile:
            return {}

        # Record usage
        await LLMProfileService.record_profile_usage(profile.name)

        return profile.to_openai_params()

    @staticmethod
    async def clone_profile(
        source_name: str, new_name: str, new_title: Optional[str] = None
    ) -> Optional[LLMProfile]:
        """Clone an existing profile with a new name."""
        source_profile = await LLMProfileService.get_profile(source_name)
        if not source_profile:
            return None

        new_profile = await LLMProfileService.create_profile(
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

        logger.info(f"Cloned LLM profile {source_name} to {new_name}")
        return new_profile

    @staticmethod
    async def get_profile_stats() -> Dict[str, Any]:
        """Get profile usage statistics."""
        async with AsyncSessionLocal() as db:
            # Total counts
            total_profiles = await db.scalar(select(func.count(LLMProfile.id)))
            active_profiles = await db.scalar(
                select(func.count(LLMProfile.id)).where(LLMProfile.is_active == True)
            )

            # Most used profiles
            most_used = await db.execute(
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
            recently_used = await db.execute(
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
            default_profile = await LLMProfileService.get_default_profile()

            return {
                "total_profiles": total_profiles,
                "active_profiles": active_profiles,
                "inactive_profiles": total_profiles - active_profiles,
                "default_profile": default_profile.name if default_profile else None,
                "most_used": most_used_list,
                "recently_used": recently_used_list,
            }

    @staticmethod
    async def validate_parameters(**parameters) -> Dict[str, str]:
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
            if presence_penalty is not None and (
                presence_penalty < -2.0 or presence_penalty > 2.0
            ):
                errors["presence_penalty"] = (
                    "presence_penalty must be between -2.0 and 2.0"
                )

        if "frequency_penalty" in parameters:
            frequency_penalty = parameters["frequency_penalty"]
            if frequency_penalty is not None and (
                frequency_penalty < -2.0 or frequency_penalty > 2.0
            ):
                errors["frequency_penalty"] = (
                    "frequency_penalty must be between -2.0 and 2.0"
                )

        return errors

    @staticmethod
    async def _ensure_default_profile() -> bool:
        """Ensure there is at least one default LLM profile active."""
        async with AsyncSessionLocal() as db:
            # Check if there's any active default profile
            default_profile = await db.execute(
                select(LLMProfile).where(
                    and_(LLMProfile.is_default == True, LLMProfile.is_active == True)
                )
            )
            default_profile = default_profile.scalar_one_or_none()

            if default_profile:
                return True  # Already have a default

            # Find the most recently used active profile to make default
            candidate = await db.execute(
                select(LLMProfile)
                .where(LLMProfile.is_active == True)
                .order_by(LLMProfile.usage_count.desc(), LLMProfile.created_at.desc())
                .limit(1)
            )
            candidate = candidate.scalar_one_or_none()

            if candidate:
                candidate.is_default = True
                await db.commit()
                logger.info(
                    f"Automatically assigned new default LLM profile: {candidate.name}"
                )
                return True
            else:
                logger.warning("No active LLM profiles available to set as default")
                return False
