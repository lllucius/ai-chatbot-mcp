"Service layer for prompt_service business logic."

from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, or_, select, update
from ..database import AsyncSessionLocal
from ..models.prompt import Prompt
from ..utils.logging import get_api_logger

logger = get_api_logger("prompt_service")


class PromptService:
    "Prompt service for business logic operations."

    @staticmethod
    async def create_prompt(
        name: str,
        title: str,
        content: str,
        description: Optional[str] = None,
        is_default: bool = False,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Prompt:
        "Create new prompt."
        async with AsyncSessionLocal() as db:
            if is_default:
                (await db.execute(update(Prompt).values(is_default=False)))
            prompt = Prompt(
                name=name,
                title=title,
                content=content,
                description=description,
                is_default=is_default,
                category=category,
            )
            if tags:
                prompt.tag_list = tags
            db.add(prompt)
            (await db.commit())
            (await db.refresh(prompt))
            logger.info(f"Created prompt: {name}")
            return prompt

    @staticmethod
    async def get_prompt(name: str) -> Optional[Prompt]:
        "Get prompt data."
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Prompt).where((Prompt.name == name)))
            return result.scalar_one_or_none()

    @staticmethod
    async def get_default_prompt() -> Optional[Prompt]:
        "Get default prompt data."
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Prompt).where(Prompt.is_default))
            return result.scalar_one_or_none()

    @staticmethod
    async def list_prompts(
        active_only: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Prompt]:
        "List prompts entries."
        async with AsyncSessionLocal() as db:
            query = select(Prompt)
            filters = []
            if active_only:
                filters.append(Prompt.is_active)
            if category:
                filters.append((Prompt.category == category))
            if search:
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        Prompt.name.ilike(search_term),
                        Prompt.title.ilike(search_term),
                        Prompt.content.ilike(search_term),
                        Prompt.tags.ilike(search_term),
                    )
                )
            if filters:
                query = query.where(and_(*filters))
            result = await db.execute(query.order_by(Prompt.name))
            return list(result.scalars().all())

    @staticmethod
    async def update_prompt(name: str, **updates) -> Optional[Prompt]:
        "Update existing prompt."
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(select(Prompt).where((Prompt.name == name)))
            prompt = prompt.scalar_one_or_none()
            if not prompt:
                return None
            if updates.get("is_default"):
                (await db.execute(update(Prompt).values(is_default=False)))
            if ("tags" in updates) and isinstance(updates["tags"], list):
                prompt.tag_list = updates.pop("tags")
            for key, value in updates.items():
                if hasattr(prompt, key):
                    setattr(prompt, key, value)
            (await db.commit())
            (await db.refresh(prompt))
            logger.info(f"Updated prompt: {name}")
            return prompt

    @staticmethod
    async def delete_prompt(name: str) -> bool:
        "Delete prompt."
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(select(Prompt).where((Prompt.name == name)))
            prompt = prompt.scalar_one_or_none()
            if not prompt:
                return False
            was_default = prompt.is_default
            (await db.delete(prompt))
            (await db.commit())
            if was_default:
                (await PromptService._ensure_default_prompt())
            logger.info(f"Deleted prompt: {name}")
            return True

    @staticmethod
    async def set_default_prompt(name: str) -> bool:
        "Set Default Prompt operation."
        async with AsyncSessionLocal() as db:
            (await db.execute(update(Prompt).values(is_default=False)))
            result = await db.execute(
                update(Prompt).where((Prompt.name == name)).values(is_default=True)
            )
            (await db.commit())
            if result.rowcount > 0:
                logger.info(f"Set default prompt: {name}")
                return True
            return False

    @staticmethod
    async def activate_prompt(name: str) -> bool:
        "Activate Prompt operation."
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(Prompt).where((Prompt.name == name)).values(is_active=True)
            )
            (await db.commit())
            if result.rowcount > 0:
                logger.info(f"Activated prompt: {name}")
                return True
            return False

    @staticmethod
    async def deactivate_prompt(name: str) -> bool:
        "Deactivate Prompt operation."
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(select(Prompt).where((Prompt.name == name)))
            prompt = prompt.scalar_one_or_none()
            if not prompt:
                return False
            was_default = prompt.is_default
            result = await db.execute(
                update(Prompt).where((Prompt.name == name)).values(is_active=False)
            )
            (await db.commit())
            if result.rowcount > 0:
                if was_default:
                    (await PromptService._ensure_default_prompt())
                logger.info(f"Deactivated prompt: {name}")
                return True
            return False

    @staticmethod
    async def record_prompt_usage(name: str) -> bool:
        "Record Prompt Usage operation."
        async with AsyncSessionLocal() as db:
            prompt = await db.execute(select(Prompt).where((Prompt.name == name)))
            prompt = prompt.scalar_one_or_none()
            if not prompt:
                return False
            prompt.record_usage()
            (await db.commit())
            return True

    @staticmethod
    async def get_categories() -> List[str]:
        "Get categories data."
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
        "Get all tags data."
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Prompt.tags).where(Prompt.tags.isnot(None))
            )
            all_tags = set()
            for row in result.all():
                if row[0]:
                    tags = [tag.strip() for tag in row[0].split(",") if tag.strip()]
                    all_tags.update(tags)
            return sorted(list(all_tags))

    @staticmethod
    async def get_prompt_stats() -> Dict[(str, Any)]:
        "Get prompt stats data."
        async with AsyncSessionLocal() as db:
            total_prompts = await db.scalar(select(func.count(Prompt.id)))
            active_prompts = await db.scalar(
                select(func.count(Prompt.id)).where(Prompt.is_active)
            )
            most_used = await db.execute(
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
                    "last_used_at": p.last_used_at,
                }
                for p in recently_used.scalars().all()
            ]
            default_prompt = await PromptService.get_default_prompt()
            return {
                "total_prompts": total_prompts,
                "active_prompts": active_prompts,
                "inactive_prompts": (total_prompts - active_prompts),
                "default_prompt": (default_prompt.name if default_prompt else None),
                "most_used": most_used_list,
                "recently_used": recently_used_list,
                "categories": (await PromptService.get_categories()),
                "total_tags": len((await PromptService.get_all_tags())),
            }

    @staticmethod
    async def _ensure_default_prompt() -> bool:
        "Ensure Default Prompt operation."
        async with AsyncSessionLocal() as db:
            default_prompt = await db.execute(
                select(Prompt).where(and_(Prompt.is_default, Prompt.is_active))
            )
            default_prompt = default_prompt.scalar_one_or_none()
            if default_prompt:
                return True
            candidate = await db.execute(
                select(Prompt)
                .where(Prompt.is_active)
                .order_by(Prompt.usage_count.desc(), Prompt.created_at.desc())
                .limit(1)
            )
            candidate = candidate.scalar_one_or_none()
            if candidate:
                candidate.is_default = True
                (await db.commit())
                logger.info(
                    f"Automatically assigned new default prompt: {candidate.name}"
                )
                return True
            else:
                logger.warning("No active prompts available to set as default")
                return False
