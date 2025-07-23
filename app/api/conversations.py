"""
Conversation and chat API endpoints.

This module provides endpoints for managing conversations, sending messages,
and interacting with the AI assistant with RAG capabilities and registry
integration for prompts, LLM profiles, and MCP tools.
"""

import json
import time
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError, ValidationError
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from ..schemas.conversation import (ChatRequest, ChatResponse,
                                    ConversationCreate, ConversationResponse,
                                    ConversationStats, ConversationUpdate,
                                    MessageResponse)
from ..services.conversation import ConversationService

router = APIRouter(tags=["conversations"])


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(db)


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Create a new conversation.

    Creates a new conversation thread for the current user.
    """
    try:
        conversation = await conversation_service.create_conversation(
            request, current_user.id
        )
        return ConversationResponse.model_validate(conversation)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    List user's conversations with pagination.

    Returns paginated list of conversations owned by the current user
    with optional filtering by active status.
    """
    try:
        conversations, total = await conversation_service.list_conversations(
            user_id=current_user.id, page=page, size=size, active_only=active_only
        )

        conversation_responses = [
            ConversationResponse.model_validate(conv) for conv in conversations
        ]

        return PaginatedResponse(
            items=conversation_responses,
            pagination=PaginationParams(page=page, per_page=size),
            total=total,
            success=True,
            message="Conversations retrieved successfully",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations",
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get conversation by ID.

    Returns detailed information about a specific conversation
    owned by the current user.
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id, current_user.id
        )
        return ConversationResponse.model_validate(conversation)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Update conversation metadata.

    Allows updating conversation title, active status, and metadata.
    """
    try:
        conversation = await conversation_service.update_conversation(
            conversation_id, request, current_user.id
        )
        return ConversationResponse.model_validate(conversation)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation update failed",
        )


@router.delete("/{conversation_id}", response_model=BaseResponse)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Delete conversation and all messages.

    Permanently deletes the conversation and all associated messages.
    """
    try:
        success = await conversation_service.delete_conversation(
            conversation_id, current_user.id
        )

        if success:
            return BaseResponse(
                success=True, message="Conversation deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation deletion failed",
        )


@router.get(
    "/{conversation_id}/messages", response_model=PaginatedResponse[MessageResponse]
)
async def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get messages in a conversation.

    Returns paginated list of messages in the specified conversation.
    """
    try:
        messages, total = await conversation_service.get_messages(
            conversation_id, current_user.id, page=page, size=size
        )

        message_responses = [MessageResponse.model_validate(msg) for msg in messages]

        return PaginatedResponse(
            items=message_responses,
            pagination=PaginationParams(page=page, per_page=size),
            total=total,
            success=True,
            message="Messages retrieved successfully",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages",
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Send a message and get AI response.

    Sends a user message to the AI assistant and returns the response.
    Supports RAG (Retrieval-Augmented Generation) for context-aware responses,
    tool calling, and registry-based prompt/profile management.
    """
    try:
        start_time = time.time()

        # Process chat request
        result = await conversation_service.process_chat(request, current_user.id)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        return ChatResponse(
            success=True,
            message="Chat response generated successfully with registry integration",
            ai_message=result["ai_message"],
            conversation=result["conversation"],
            usage=result.get("usage"),
            rag_context=result.get("rag_context"),
            tool_calls_made=result.get("tool_calls_made"),
            tool_call_summary=result.get("tool_call_summary"),
            response_time_ms=response_time_ms,
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Send a message and get a streaming AI response.

    Returns a Server-Sent Events (SSE) stream of the AI response as it's generated,
    providing real-time feedback to the user.
    """
    try:

        async def generate_response():
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Generating response...'})}\n\n"

            # Process chat request with streaming
            async for chunk in conversation_service.process_chat_stream(
                request, current_user.id
            ):
                if chunk.get("type") == "content":
                    # Stream content chunks
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.get('content', '')})}\n\n"
                elif chunk.get("type") == "tool_call":
                    # Stream tool call information
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': chunk.get('tool'), 'result': chunk.get('result')})}\n\n"
                elif chunk.get("type") == "complete":
                    # Send completion event with full response
                    yield f"data: {json.dumps({'type': 'complete', 'response': chunk.get('response')})}\n\n"
                    break

            # Send end event
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process streaming chat request: {str(e)}",
        )


@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get conversation statistics for the current user with registry insights.

    Returns statistics about the user's conversations and messages, plus
    insights from prompt and profile registries.
    """
    try:
        stats = await conversation_service.get_user_stats(current_user.id)
        return ConversationStats.model_validate(stats)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation stats",
        )


@router.get("/registry-stats", response_model=Dict[str, Any])
async def get_registry_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get registry statistics showing prompt, profile, and tool usage.

    Returns comprehensive statistics about registry usage including:
    - Active prompts and most used prompts
    - Active LLM profiles and usage patterns
    - MCP tools and server status
    """
    try:
        registry_stats = await conversation_service._get_registry_stats()

        return {
            "success": True,
            "message": "Registry statistics retrieved successfully",
            "data": registry_stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve registry statistics: {str(e)}",
        )
