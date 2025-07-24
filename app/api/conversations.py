"API endpoints for conversations operations."

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
from ..schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationStats,
    ConversationUpdate,
    MessageResponse,
)
from ..services.conversation import ConversationService

router = APIRouter(tags=["conversations"])


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    "Get conversation service data."
    return ConversationService(db)


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    "Create new conversation."
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
    "List conversations entries."
    try:
        (conversations, total) = await conversation_service.list_conversations(
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
    "Get conversation data."
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
    "Update existing conversation."
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
    "Delete conversation."
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
    "Get messages data."
    try:
        (messages, total) = await conversation_service.get_messages(
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
    "Chat operation."
    try:
        start_time = time.time()
        result = await conversation_service.process_chat(request, current_user.id)
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
    "Chat Stream operation."
    try:

        async def generate_response():
            "Generate Response operation."
            (
                yield f"""data: {json.dumps({'type': 'start', 'message': 'Generating response...'})}

"""
            )
            async for chunk in conversation_service.process_chat_stream(
                request, current_user.id
            ):
                if chunk.get("type") == "content":
                    (
                        yield f"""data: {json.dumps({'type': 'content', 'content': chunk.get('content', '')})}

"""
                    )
                elif chunk.get("type") == "tool_call":
                    (
                        yield f"""data: {json.dumps({'type': 'tool_call', 'tool': chunk.get('tool'), 'result': chunk.get('result')})}

"""
                    )
                elif chunk.get("type") == "complete":
                    (
                        yield f"""data: {json.dumps({'type': 'complete', 'response': chunk.get('response')})}

"""
                    )
                    break
            (
                yield f"""data: {json.dumps({'type': 'end'})}

"""
            )

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
    "Get conversation stats data."
    try:
        stats = await conversation_service.get_user_stats(current_user.id)
        return ConversationStats.model_validate(stats)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation stats",
        )


@router.get("/registry-stats", response_model=Dict[(str, Any)])
async def get_registry_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    "Get registry stats data."
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
