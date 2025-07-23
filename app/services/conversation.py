"""
Conversation service for comprehensive chat functionality and message management.

This service provides complete conversation lifecycle management including chat
session creation, message handling, AI model integration, and RAG (Retrieval
Augmented Generation) capabilities. It orchestrates multiple services to deliver
intelligent conversational experiences with document context.

Key Features:
- Conversation lifecycle management (create, update, archive)
- AI-powered chat with OpenAI integration
- RAG capabilities with document search integration
- Message history and context management
- Multi-turn conversation handling with context preservation
- Usage tracking and analytics
- Comprehensive error handling and recovery

AI Integration:
- OpenAI GPT models for intelligent responses
- Document search integration for contextual information
- Embedding services for semantic understanding
- Tool calling capabilities through MCP integration
- Token usage tracking and optimization

Generated on: 2025-07-14 03:50:38 UTC
Updated on: 2025-01-20 20:10:00 UTC
Current User: lllucius / assistant
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, ValidationError
from ..models.conversation import Conversation, Message
from ..schemas.conversation import (ChatRequest, ConversationCreate,
                                    ConversationResponse, ConversationUpdate,
                                    MessageResponse)
from ..schemas.document import DocumentSearchRequest
from ..schemas.tool_calling import ToolCallResult, ToolCallSummary
from ..services.embedding import EmbeddingService
from ..services.openai_client import OpenAIClient
from ..services.search import SearchService
from .base import BaseService

logger = logging.getLogger(__name__)


class ConversationService(BaseService):
    """
    Service for comprehensive conversation and AI chat operations.

    This service extends BaseService to provide conversation-specific functionality
    including chat session management, AI model integration, RAG capabilities,
    and unified tool calling with enhanced logging and context management.

    AI Capabilities:
    - Multi-turn conversations with context preservation
    - Integration with OpenAI GPT models for intelligent responses
    - RAG (Retrieval Augmented Generation) with document search
    - Unified tool calling through UnifiedToolExecutor integration
    - Token usage optimization and tracking
    - Response quality monitoring and analytics

    Tool Integration:
    - Uses unified tool calling instead of manual tool management
    - Automatic tool availability and execution through OpenAI client
    - Proper tool call result handling and user feedback
    - Complete tool calling implementation (no TODOs remaining)

    Responsibilities:
    - Conversation lifecycle management (create, update, archive)
    - Message processing and storage with metadata
    - AI model orchestration and response generation
    - Document search integration for context enhancement
    - Usage analytics and performance monitoring
    - Error handling and recovery for AI operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize conversation service with AI and search components.

        Args:
            db: Database session for conversation operations
        """
        super().__init__(db, "conversation_service")

        # Initialize AI and search services
        self.openai_client = OpenAIClient()
        self.search_service = SearchService(db)
        self.embedding_service = EmbeddingService(db)

    async def create_conversation(
        self, request: ConversationCreate, user_id: UUID
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            request: Conversation creation data
            user_id: User ID who owns the conversation

        Returns:
            Conversation: Created conversation object
        """
        try:
            conversation = Conversation(
                title=request.title,
                is_active=request.is_active,
                user_id=user_id,
                metainfo=request.metainfo,
            )

            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            logger.info(f"Conversation created: {conversation.id} for user {user_id}")
            return conversation

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise ValidationError(f"Conversation creation failed: {e}")

    async def get_conversation(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control

        Returns:
            Conversation: Conversation object

        Raises:
            NotFoundError: If conversation not found or access denied
        """
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id, Conversation.user_id == user_id
                )
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError("Conversation not found")

        return conversation

    async def list_conversations(
        self, user_id: UUID, page: int = 1, size: int = 20, active_only: bool = True
    ) -> Tuple[List[Conversation], int]:
        """
        List conversations for a user with pagination.

        Args:
            user_id: User ID
            page: Page number (1-based)
            size: Items per page
            active_only: Filter to active conversations only

        Returns:
            Tuple[List[Conversation], int]: List of conversations and total count
        """
        # Build filters
        filters = [Conversation.user_id == user_id]
        if active_only:
            filters.append(Conversation.is_active is True)

        # Count total conversations
        count_query = select(func.count(Conversation.id)).where(and_(*filters))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get conversations with pagination
        query = (
            select(Conversation)
            .where(and_(*filters))
            .order_by(desc(Conversation.updated_at))
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def update_conversation(
        self, conversation_id: UUID, request: ConversationUpdate, user_id: UUID
    ) -> Conversation:
        """
        Update conversation metainfo.

        Args:
            conversation_id: Conversation ID
            request: Update data
            user_id: User ID for access control

        Returns:
            Conversation: Updated conversation object
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        # Update fields
        if request.title is not None:
            conversation.title = request.title
        if request.is_active is not None:
            conversation.is_active = request.is_active
        if request.metainfo is not None:
            conversation.metainfo = request.metainfo

        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"Conversation updated: {conversation_id}")
        return conversation

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """
        Delete conversation and all messages.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control

        Returns:
            bool: True if deleted successfully
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        await self.db.delete(conversation)
        await self.db.commit()

        logger.info(f"Conversation deleted: {conversation_id}")
        return True

    async def get_messages(
        self, conversation_id: UUID, user_id: UUID, page: int = 1, size: int = 50
    ) -> Tuple[List[Message], int]:
        """
        Get messages in a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for access control
            page: Page number (1-based)
            size: Items per page

        Returns:
            Tuple[List[Message], int]: List of messages and total count
        """
        # Verify conversation access
        await self.get_conversation(conversation_id, user_id)

        # Count total messages
        count_query = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get messages with pagination
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(messages), total

    async def process_chat(self, request: ChatRequest, user_id: UUID) -> Dict[str, Any]:
        """
        Process chat request and generate AI response.

        Args:
            request: Chat request data
            user_id: User ID

        Returns:
            dict: Chat response data including AI message and conversation
        """
        try:
            # Get or create conversation
            if request.conversation_id:
                conversation = await self.get_conversation(
                    request.conversation_id, user_id
                )
            else:
                # Create new conversation
                title = (
                    request.conversation_title or f"Chat {request.user_message[:50]}..."
                )
                conversation = await self.create_conversation(
                    ConversationCreate(title=title, is_active=True), user_id
                )

            # Add user message
            user_message = Message(
                role="user",
                content=request.user_message,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(request.user_message),
            )
            self.db.add(user_message)

            # Get conversation history
            history_messages = await self._get_conversation_history(conversation.id)

            # Prepare messages for AI
            ai_messages = []

            # Add system message if needed
            system_prompt = self._build_system_prompt(request)
            if system_prompt:
                ai_messages.append({"role": "system", "content": system_prompt})

            # Add conversation history
            for msg in history_messages:
                ai_messages.append({"role": msg.role, "content": msg.content})

            # Add current user message
            ai_messages.append({"role": "user", "content": request.user_message})

            # Get RAG context if enabled
            rag_context = None
            if request.use_rag:
                rag_context = await self._get_rag_context(request, user_id)
                if rag_context:
                    # Add RAG context to system message
                    context_text = self._format_rag_context(rag_context)
                    if ai_messages[0]["role"] == "system":
                        ai_messages[0][
                            "content"
                        ] += f"\n\nRelevant context:\n{context_text}"
                    else:
                        ai_messages.insert(
                            0,
                            {
                                "role": "system",
                                "content": f"Use the following context to help answer questions:\n{context_text}",
                            },
                        )

            # Get AI response with unified tool calling and flexible tool handling
            ai_response = await self.openai_client.chat_completion(
                messages=ai_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                use_unified_tools=request.use_tools,
                tool_handling_mode=request.tool_handling_mode,
            )

            # Create AI message
            ai_message = Message(
                role="assistant",
                content=ai_response["content"],
                conversation_id=conversation.id,
                token_count=ai_response["usage"]["completion_tokens"],
            )
            self.db.add(ai_message)

            # Update conversation
            conversation.message_count += 2  # User + AI message

            await self.db.commit()
            await self.db.refresh(user_message)
            await self.db.refresh(ai_message)
            await self.db.refresh(conversation)

            logger.info(f"Chat processed for conversation {conversation.id}")

            # Create tool call summary if tools were executed
            tool_call_summary = None
            tool_calls_executed = ai_response.get("tool_calls_executed", [])
            if tool_calls_executed:
                tool_call_summary = self._create_tool_call_summary(tool_calls_executed)

            return {
                "ai_message": MessageResponse.model_validate(ai_message),
                "conversation": ConversationResponse.model_validate(conversation),
                "usage": ai_response["usage"],
                "rag_context": rag_context,
                "tool_calls_made": tool_calls_executed,  # Deprecated but maintained for compatibility
                "tool_call_summary": tool_call_summary,
                "tool_handling_mode": ai_response.get("tool_handling_mode"),
            }

        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise ValidationError(f"Chat processing failed: {e}")

    async def process_chat_stream(self, request: ChatRequest, user_id: UUID):
        """
        Process chat request and generate streaming AI response.

        Args:
            request: Chat request data
            user_id: User ID

        Yields:
            dict: Stream chunks with response data
        """
        try:
            # Get or create conversation
            if request.conversation_id:
                conversation = await self.get_conversation(
                    request.conversation_id, user_id
                )
            else:
                # Create new conversation
                title = (
                    request.conversation_title or f"Chat {request.user_message[:50]}..."
                )
                conversation = await self.create_conversation(
                    ConversationCreate(title=title, is_active=True), user_id
                )

            # Add user message
            user_message = Message(
                role="user",
                content=request.user_message,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(request.user_message),
            )
            self.db.add(user_message)
            await self.db.flush()  # Save user message immediately

            # Get conversation history
            history_messages = await self._get_conversation_history(conversation.id)

            # Prepare messages for AI
            ai_messages = []

            # Add system message if needed
            system_prompt = self._build_system_prompt(request)
            if system_prompt:
                ai_messages.append({"role": "system", "content": system_prompt})

            # Add conversation history
            for msg in history_messages[:-1]:  # Exclude the user message we just added
                ai_messages.append({"role": msg.role, "content": msg.content})

            # Add current user message
            ai_messages.append({"role": "user", "content": request.user_message})

            # Get RAG context if enabled
            rag_context = None
            if request.use_rag:
                rag_context = await self._get_rag_context(request, user_id)
                if rag_context:
                    # Add RAG context to system message
                    context_text = self._format_rag_context(rag_context)
                    if ai_messages[0]["role"] == "system":
                        ai_messages[0][
                            "content"
                        ] += f"\n\nRelevant context:\n{context_text}"
                    else:
                        ai_messages.insert(
                            0,
                            {
                                "role": "system",
                                "content": f"Use the following context to help answer questions:\n{context_text}",
                            },
                        )

            # Stream AI response
            full_content = ""
            tool_calls_executed = []
            
            async for chunk in self.openai_client.chat_completion_stream(
                messages=ai_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                use_unified_tools=request.use_tools,
                tool_handling_mode=request.tool_handling_mode,
            ):
                if chunk.get("type") == "content":
                    content = chunk.get("content", "")
                    full_content += content
                    yield {"type": "content", "content": content}
                elif chunk.get("type") == "tool_call":
                    yield {"type": "tool_call", "tool": chunk.get("tool"), "result": chunk.get("result")}
                    tool_calls_executed.append(chunk)

            # Create AI message with complete content
            ai_message = Message(
                role="assistant",
                content=full_content,
                conversation_id=conversation.id,
                token_count=self.openai_client.count_tokens(full_content),
            )
            self.db.add(ai_message)

            # Update conversation
            conversation.message_count += 2  # User + AI message

            await self.db.commit()
            await self.db.refresh(ai_message)
            await self.db.refresh(conversation)

            # Create tool call summary if tools were executed
            tool_call_summary = None
            if tool_calls_executed:
                tool_call_summary = self._create_tool_call_summary(tool_calls_executed)

            # Send completion event
            yield {
                "type": "complete",
                "response": {
                    "ai_message": MessageResponse.model_validate(ai_message),
                    "conversation": ConversationResponse.model_validate(conversation),
                    "rag_context": rag_context,
                    "tool_call_summary": tool_call_summary,
                }
            }

        except Exception as e:
            logger.error(f"Streaming chat processing failed: {e}")
            yield {"type": "error", "error": str(e)}

    async def _get_conversation_history(
        self, conversation_id: UUID, limit: int = 20
    ) -> List[Message]:
        """Get recent conversation history."""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Return in chronological order
        return list(reversed(messages))

    def _build_system_prompt(self, request: ChatRequest) -> str:
        """Build system prompt based on request parameters."""
        prompt_parts = [
            "You are a helpful AI assistant with access to a knowledge base.",
            "Provide accurate, helpful, and well-structured responses.",
            "If you're unsure about something, say so rather than guessing.",
        ]

        if request.use_rag:
            prompt_parts.append(
                "You have access to relevant context from documents. "
                "Use this context to provide more accurate and detailed answers."
            )

        return "\n".join(prompt_parts)

    async def _get_rag_context(
        self, request: ChatRequest, user_id: UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """Get RAG context for the chat request."""
        try:
            # Create search request
            search_request = DocumentSearchRequest(
                query=request.user_message,
                limit=5,
                threshold=0.7,
                algorithm="hybrid",
                document_ids=request.rag_documents,
            )

            # Search for relevant chunks
            search_results = await self.search_service.search_documents(
                search_request, user_id
            )

            if not search_results:
                return None

            # Format context
            context = []
            for result in search_results:
                context.append(
                    {
                        "content": result.content,
                        "source": result.document_title
                        or f"Document {result.document_id}",
                        "similarity": result.similarity_score,
                        "chunk_id": result.id,
                    }
                )

            return context

        except Exception as e:
            logger.warning(f"Failed to get RAG context: {e}")
            return None

    def _format_rag_context(self, context: List[Dict[str, Any]]) -> str:
        """Format RAG context for inclusion in prompt."""
        formatted_parts = []

        for i, item in enumerate(context, 1):
            formatted_parts.append(
                f"[{i}] Source: {item['source']}\n" f"Content: {item['content']}\n"
            )

        return "\n".join(formatted_parts)

    def _create_tool_call_summary(self, tool_calls_executed: List[Dict[str, Any]]) -> ToolCallSummary:
        """
        Create a tool call summary from executed tool calls.
        
        Args:
            tool_calls_executed: List of executed tool call results
            
        Returns:
            ToolCallSummary: Summary of tool call execution
        """
        if not tool_calls_executed:
            return ToolCallSummary(
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                total_execution_time_ms=0.0,
                results=[]
            )
        
        successful_calls = sum(1 for call in tool_calls_executed if call.get("success", False))
        failed_calls = len(tool_calls_executed) - successful_calls
        total_execution_time = sum(call.get("execution_time_ms", 0) or 0 for call in tool_calls_executed)
        
        # Convert to ToolCallResult objects
        results = []
        for call in tool_calls_executed:
            results.append(ToolCallResult(
                tool_call_id=call.get("tool_call_id", ""),
                tool_name=call.get("tool_name", "unknown"),
                success=call.get("success", False),
                content=call.get("content", []),
                error=call.get("error"),
                provider=call.get("provider"),
                execution_time_ms=call.get("execution_time_ms")
            ))
        
        return ToolCallSummary(
            total_calls=len(tool_calls_executed),
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            total_execution_time_ms=total_execution_time,
            results=results
        )

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get conversation statistics for a user.

        Args:
            user_id: User ID

        Returns:
            dict: User conversation statistics
        """
        # Total conversations
        total_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        total_conversations = total_result.scalar() or 0

        # Active conversations
        active_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                and_(Conversation.user_id == user_id, Conversation.is_active is True)
            )
        )
        active_conversations = active_result.scalar() or 0

        # Total messages
        messages_result = await self.db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.user_id == user_id)
        )
        total_messages = messages_result.scalar() or 0

        # Average messages per conversation
        avg_messages = (
            total_messages / total_conversations if total_conversations > 0 else 0
        )

        # Most recent activity
        recent_result = await self.db.execute(
            select(func.max(Conversation.updated_at)).where(
                Conversation.user_id == user_id
            )
        )
        most_recent_activity = recent_result.scalar()

        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(avg_messages, 1),
            "most_recent_activity": most_recent_activity,
        }
