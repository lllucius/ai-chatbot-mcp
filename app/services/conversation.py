"Service layer for conversation business logic."

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import NotFoundError, ValidationError
from ..models.conversation import Conversation, Message
from ..schemas.conversation import (
    ChatRequest,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from ..schemas.document import DocumentSearchRequest
from ..schemas.tool_calling import ToolCallResult, ToolCallSummary
from ..services.embedding import EmbeddingService
from ..services.mcp_client import get_mcp_client
from ..services.llm_profile_service import LLMProfileService
from ..services.openai_client import OpenAIClient
from ..services.prompt_service import PromptService
from ..services.search import SearchService
from .base import BaseService

logger = logging.getLogger(__name__)


class ConversationService(BaseService):
    "Conversation service for business logic operations."

    def __init__(self, db: AsyncSession):
        "Initialize class instance."
        super().__init__(db, "conversation_service")
        self.openai_client = OpenAIClient()
        self.search_service = SearchService(db)
        self.embedding_service = EmbeddingService(db)

    async def create_conversation(
        self, request: ConversationCreate, user_id: UUID
    ) -> Conversation:
        "Create new conversation."
        try:
            conversation = Conversation(
                title=request.title,
                is_active=request.is_active,
                user_id=user_id,
                metainfo=request.metainfo,
            )
            self.db.add(conversation)
            (await self.db.commit())
            (await self.db.refresh(conversation))
            logger.info(f"Conversation created: {conversation.id} for user {user_id}")
            return conversation
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise ValidationError(f"Conversation creation failed: {e}")

    async def get_conversation(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation:
        "Get conversation data."
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    (Conversation.id == conversation_id),
                    (Conversation.user_id == user_id),
                )
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise NotFoundError("Conversation not found")
        return conversation

    async def list_conversations(
        self, user_id: UUID, page: int = 1, size: int = 20, active_only: bool = True
    ) -> Tuple[(List[Conversation], int)]:
        "List conversations entries."
        filters = [Conversation.user_id == user_id]
        if active_only:
            filters.append((Conversation.is_active is True))
        count_query = select(func.count(Conversation.id)).where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = (
            select(Conversation)
            .where(and_(*filters))
            .order_by(desc(Conversation.updated_at))
            .offset(((page - 1) * size))
            .limit(size)
        )
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        return (list(conversations), total)

    async def update_conversation(
        self, conversation_id: UUID, request: ConversationUpdate, user_id: UUID
    ) -> Conversation:
        "Update existing conversation."
        conversation = await self.get_conversation(conversation_id, user_id)
        if request.title is not None:
            conversation.title = request.title
        if request.is_active is not None:
            conversation.is_active = request.is_active
        if request.metainfo is not None:
            conversation.metainfo = request.metainfo
        (await self.db.commit())
        (await self.db.refresh(conversation))
        logger.info(f"Conversation updated: {conversation_id}")
        return conversation

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        "Delete conversation."
        conversation = await self.get_conversation(conversation_id, user_id)
        (await self.db.delete(conversation))
        (await self.db.commit())
        logger.info(f"Conversation deleted: {conversation_id}")
        return True

    async def get_messages(
        self, conversation_id: UUID, user_id: UUID, page: int = 1, size: int = 50
    ) -> Tuple[(List[Message], int)]:
        "Get messages data."
        (await self.get_conversation(conversation_id, user_id))
        count_query = select(func.count(Message.id)).where(
            (Message.conversation_id == conversation_id)
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = (
            select(Message)
            .where((Message.conversation_id == conversation_id))
            .order_by(Message.created_at)
            .offset(((page - 1) * size))
            .limit(size)
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()
        return (list(messages), total)

    async def process_chat(
        self, request: ChatRequest, user_id: UUID
    ) -> Dict[(str, Any)]:
        "Process chat operations."
        try:
            if request.conversation_id:
                conversation = await self.get_conversation(
                    request.conversation_id, user_id
                )
            else:
                title = (
                    request.conversation_title or f"Chat {request.user_message[:50]}..."
                )
                conversation = await self.create_conversation(
                    ConversationCreate(title=title, is_active=True), user_id
                )
            user_message = Message(
                role="user",
                content=request.user_message,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(request.user_message),
            )
            self.db.add(user_message)
            history_messages = await self._get_conversation_history(conversation.id)
            ai_messages = []
            system_prompt = await self._build_system_prompt(request)
            if system_prompt:
                ai_messages.append({"role": "system", "content": system_prompt})
            for msg in history_messages:
                ai_messages.append({"role": msg.role, "content": msg.content})
            ai_messages.append({"role": "user", "content": request.user_message})
            rag_context = None
            if request.use_rag:
                rag_context = await self._get_rag_context(request, user_id)
                if rag_context:
                    context_text = self._format_rag_context(rag_context)
                    if ai_messages[0]["role"] == "system":
                        ai_messages[0][
                            "content"
                        ] += f"""

Relevant context:
{context_text}"""
                    else:
                        ai_messages.insert(
                            0,
                            {
                                "role": "system",
                                "content": f"""Use the following context to help answer questions:
{context_text}""",
                            },
                        )
            llm_profile = None
            try:
                if request.llm_profile:
                    llm_profile = request.llm_profile
                elif request.profile_name:
                    llm_profile = await LLMProfileService.get_profile(
                        request.profile_name
                    )
                else:
                    llm_profile = await LLMProfileService.get_default_profile()
                if llm_profile:
                    (await LLMProfileService.record_profile_usage(llm_profile.name))
            except Exception as e:
                logger.warning(f"Failed to get LLM profile: {e}")
                llm_profile = None
            openai_params = {"llm_profile": llm_profile}
            if request.use_tools:
                try:
                    mcp_client = await get_mcp_client()
                    openai_params["use_unified_tools"] = True
                    openai_params["tool_handling_mode"] = request.tool_handling_mode
                except Exception as e:
                    logger.warning(f"Failed to get MCP client: {e}")
                    openai_params["use_unified_tools"] = request.use_tools
                    openai_params["tool_handling_mode"] = request.tool_handling_mode
            else:
                openai_params["use_unified_tools"] = False
            ai_response = await self.openai_client.chat_completion(
                messages=ai_messages, **openai_params
            )
            ai_message = Message(
                role="assistant",
                content=ai_response["content"],
                conversation_id=conversation.id,
                token_count=ai_response["usage"]["completion_tokens"],
            )
            self.db.add(ai_message)
            conversation.message_count += 2
            (await self.db.commit())
            (await self.db.refresh(user_message))
            (await self.db.refresh(ai_message))
            (await self.db.refresh(conversation))
            logger.info(f"Chat processed for conversation {conversation.id}")
            tool_call_summary = None
            tool_calls_executed = ai_response.get("tool_calls_executed", [])
            if tool_calls_executed:
                tool_call_summary = self._create_tool_call_summary(tool_calls_executed)
            return {
                "ai_message": MessageResponse.model_validate(ai_message),
                "conversation": ConversationResponse.model_validate(conversation),
                "usage": ai_response["usage"],
                "rag_context": rag_context,
                "tool_calls_made": tool_calls_executed,
                "tool_call_summary": tool_call_summary,
                "tool_handling_mode": ai_response.get("tool_handling_mode"),
            }
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise ValidationError(f"Chat processing failed: {e}")

    async def process_chat_stream(self, request: ChatRequest, user_id: UUID):
        "Process chat stream operations."
        try:
            if request.conversation_id:
                conversation = await self.get_conversation(
                    request.conversation_id, user_id
                )
            else:
                title = (
                    request.conversation_title or f"Chat {request.user_message[:50]}..."
                )
                conversation = await self.create_conversation(
                    ConversationCreate(title=title, is_active=True), user_id
                )
            user_message = Message(
                role="user",
                content=request.user_message,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(request.user_message),
            )
            self.db.add(user_message)
            (await self.db.flush())
            history_messages = await self._get_conversation_history(conversation.id)
            ai_messages = []
            system_prompt = await self._build_system_prompt(request)
            if system_prompt:
                ai_messages.append({"role": "system", "content": system_prompt})
            for msg in history_messages[:(-1)]:
                ai_messages.append({"role": msg.role, "content": msg.content})
            ai_messages.append({"role": "user", "content": request.user_message})
            rag_context = None
            if request.use_rag:
                rag_context = await self._get_rag_context(request, user_id)
                if rag_context:
                    context_text = self._format_rag_context(rag_context)
                    if ai_messages[0]["role"] == "system":
                        ai_messages[0][
                            "content"
                        ] += f"""

Relevant context:
{context_text}"""
                    else:
                        ai_messages.insert(
                            0,
                            {
                                "role": "system",
                                "content": f"""Use the following context to help answer questions:
{context_text}""",
                            },
                        )
            llm_profile = None
            try:
                if request.llm_profile:
                    llm_profile = request.llm_profile
                elif request.profile_name:
                    llm_profile = await LLMProfileService.get_profile(
                        request.profile_name
                    )
                else:
                    llm_profile = await LLMProfileService.get_default_profile()
                if llm_profile:
                    (await LLMProfileService.record_profile_usage(llm_profile.name))
            except Exception as e:
                logger.warning(f"Failed to get LLM profile: {e}")
                llm_profile = None
            openai_params = {"llm_profile": llm_profile}
            if request.use_tools:
                try:
                    mcp_client = await get_mcp_client()
                    openai_params["use_unified_tools"] = True
                    openai_params["tool_handling_mode"] = request.tool_handling_mode
                except Exception as e:
                    logger.warning(f"Failed to get MCP client: {e}")
                    openai_params["use_unified_tools"] = request.use_tools
                    openai_params["tool_handling_mode"] = request.tool_handling_mode
            else:
                openai_params["use_unified_tools"] = False
            full_content = ""
            tool_calls_executed = []
            async for chunk in self.openai_client.chat_completion_stream(
                messages=ai_messages, **openai_params
            ):
                if chunk.get("type") == "content":
                    content = chunk.get("content", "")
                    full_content += content
                    (yield {"type": "content", "content": content})
                elif chunk.get("type") == "tool_call":
                    (
                        yield {
                            "type": "tool_call",
                            "tool": chunk.get("tool"),
                            "result": chunk.get("result"),
                        }
                    )
                    tool_calls_executed.append(chunk)
            ai_message = Message(
                role="assistant",
                content=full_content,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(full_content),
            )
            self.db.add(ai_message)
            conversation.message_count += 2
            (await self.db.commit())
            (await self.db.refresh(ai_message))
            (await self.db.refresh(conversation))
            tool_call_summary = None
            if tool_calls_executed:
                tool_call_summary = self._create_tool_call_summary(tool_calls_executed)
            (
                yield {
                    "type": "complete",
                    "response": {
                        "ai_message": MessageResponse.model_validate(ai_message),
                        "conversation": ConversationResponse.model_validate(
                            conversation
                        ),
                        "rag_context": rag_context,
                        "tool_call_summary": tool_call_summary,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Streaming chat processing failed: {e}")
            (yield {"type": "error", "error": str(e)})

    async def _get_conversation_history(
        self, conversation_id: UUID, limit: int = 20
    ) -> List[Message]:
        "Get Conversation History operation."
        query = (
            select(Message)
            .where((Message.conversation_id == conversation_id))
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()
        return list(reversed(messages))

    async def _build_system_prompt(self, request: ChatRequest) -> str:
        "Build System Prompt operation."
        if request.prompt_name:
            try:
                prompt = await PromptService.get_prompt(request.prompt_name)
                if prompt:
                    (await PromptService.record_prompt_usage(prompt.name))
                    return prompt.content
                else:
                    logger.warning(
                        f"Prompt '{request.prompt_name}' not found, using default"
                    )
            except Exception as e:
                logger.warning(f"Failed to get prompt '{request.prompt_name}': {e}")
        try:
            default_prompt = await PromptService.get_default_prompt()
            if default_prompt:
                (await PromptService.record_prompt_usage(default_prompt.name))
                return default_prompt.content
        except Exception as e:
            logger.warning(f"Failed to get default prompt: {e}")
        prompt_parts = [
            "You are a helpful AI assistant with access to a knowledge base.",
            "Provide accurate, helpful, and well-structured responses.",
            "If you're unsure about something, say so rather than guessing.",
        ]
        if request.use_rag:
            prompt_parts.append(
                "You have access to relevant context from documents. Use this context to provide more accurate and detailed answers."
            )
        return "\n".join(prompt_parts)

    async def _get_rag_context(
        self, request: ChatRequest, user_id: UUID
    ) -> Optional[List[Dict[(str, Any)]]]:
        "Get Rag Context operation."
        try:
            search_request = DocumentSearchRequest(
                query=request.user_message,
                limit=5,
                threshold=0.7,
                algorithm="hybrid",
                document_ids=request.rag_documents,
            )
            search_results = await self.search_service.search_documents(
                search_request, user_id
            )
            if not search_results:
                return None
            context = []
            for result in search_results:
                context.append(
                    {
                        "content": result.content,
                        "source": (
                            result.document_title or f"Document {result.document_id}"
                        ),
                        "similarity": result.similarity_score,
                        "chunk_id": result.id,
                    }
                )
            return context
        except Exception as e:
            logger.warning(f"Failed to get RAG context: {e}")
            return None

    def _format_rag_context(self, context: List[Dict[(str, Any)]]) -> str:
        "Format Rag Context operation."
        formatted_parts = []
        for i, item in enumerate(context, 1):
            formatted_parts.append(
                f"""[{i}] Source: {item['source']}
Content: {item['content']}
"""
            )
        return "\n".join(formatted_parts)

    def _create_tool_call_summary(
        self, tool_calls_executed: List[Dict[(str, Any)]]
    ) -> ToolCallSummary:
        "Create Tool Call Summary operation."
        if not tool_calls_executed:
            return ToolCallSummary(
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                total_execution_time_ms=0.0,
                results=[],
            )
        successful_calls = sum(
            (1 for call in tool_calls_executed if call.get("success", False))
        )
        failed_calls = len(tool_calls_executed) - successful_calls
        total_execution_time = sum(
            ((call.get("execution_time_ms", 0) or 0) for call in tool_calls_executed)
        )
        results = []
        for call in tool_calls_executed:
            results.append(
                ToolCallResult(
                    tool_call_id=call.get("tool_call_id", ""),
                    tool_name=call.get("tool_name", "unknown"),
                    success=call.get("success", False),
                    content=call.get("content", []),
                    error=call.get("error"),
                    provider=call.get("provider"),
                    execution_time_ms=call.get("execution_time_ms"),
                )
            )
        return ToolCallSummary(
            total_calls=len(tool_calls_executed),
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            total_execution_time_ms=total_execution_time,
            results=results,
        )

    async def get_user_stats(self, user_id: UUID) -> Dict[(str, Any)]:
        "Get user stats data."
        total_result = await self.db.execute(
            select(func.count(Conversation.id)).where((Conversation.user_id == user_id))
        )
        total_conversations = total_result.scalar() or 0
        active_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    (Conversation.user_id == user_id), (Conversation.is_active is True)
                )
            )
        )
        active_conversations = active_result.scalar() or 0
        messages_result = await self.db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where((Conversation.user_id == user_id))
        )
        total_messages = messages_result.scalar() or 0
        avg_messages = (
            (total_messages / total_conversations) if (total_conversations > 0) else 0
        )
        recent_result = await self.db.execute(
            select(func.max(Conversation.updated_at)).where(
                (Conversation.user_id == user_id)
            )
        )
        most_recent_activity = recent_result.scalar()
        registry_stats = {}
        try:
            registry_stats = await self._get_registry_stats()
        except Exception as e:
            logger.warning(f"Failed to get registry stats: {e}")
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(avg_messages, 1),
            "most_recent_activity": most_recent_activity,
            "registry": registry_stats,
        }

    async def _get_registry_stats(self) -> Dict[(str, Any)]:
        "Get Registry Stats operation."
        try:
            prompt_stats = await PromptService.get_prompt_stats()
            profile_stats = await LLMProfileService.get_profile_stats()
            mcp_client = await get_mcp_client()
            health = await enhanced_client.health_check()
            return {
                "prompts": {
                    "total": prompt_stats.get("total_prompts", 0),
                    "active": prompt_stats.get("active_prompts", 0),
                    "default": prompt_stats.get("default_prompt"),
                    "most_used": prompt_stats.get("most_used", [])[:3],
                },
                "profiles": {
                    "total": profile_stats.get("total_profiles", 0),
                    "active": profile_stats.get("active_profiles", 0),
                    "default": profile_stats.get("default_profile"),
                    "most_used": profile_stats.get("most_used", [])[:3],
                },
                "tools": health.get("registry", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get registry stats: {e}")
            return {}
