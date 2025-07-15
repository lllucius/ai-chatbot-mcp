"""
Conversation and chat API endpoints.

This module provides endpoints for managing conversations, sending messages,
and interacting with the AI assistant with RAG capabilities.

Generated on: 2025-07-14 03:15:29 UTC
Current User: lllucius
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.conversation import (
    ConversationResponse,
    ConversationCreate,
    ConversationUpdate,
    MessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationStats
)
from ..schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from ..services.conversation import ConversationService
from ..core.exceptions import NotFoundError, ValidationError
from ..dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(db)


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Create a new conversation.
    
    Creates a new conversation thread for the current user.
    """
    try:
        conversation = await conversation_service.create_conversation(
            request, 
            current_user.id
        )
        return ConversationResponse.model_validate(conversation)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    List user's conversations with pagination.
    
    Returns paginated list of conversations owned by the current user
    with optional filtering by active status.
    """
    #try:
    conversations, total = await conversation_service.list_conversations(
        user_id=current_user.id,
        page=page,
        size=size,
        active_only=active_only
    )
    
    conversation_responses = [
        ConversationResponse.model_validate(conv) for conv in conversations
    ]

    print("CONTNNTNTN", conversation_responses)
    print(f"TOTAL {total} PAGE {page} SIZE {size}")
    return PaginatedResponse(
        items=conversation_responses,
        pagination=PaginationParams(page=page, per_page=size),
        total=total,
        success=True,
        message="Conversations retrieved successfully"
    )
    """ 
    return PaginatedResponse.create(
        items=conversation_responses,
        total=total,
        page=page,
        size=size,
        message="Conversations retrieved successfully"
    )
    """
    
#    except Exception as e:
#        raise HTTPException(
#            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#            detail="Failed to retrieve conversations"
#        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get conversation by ID.
    
    Returns detailed information about a specific conversation
    owned by the current user.
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id, 
            current_user.id
        )
        return ConversationResponse.model_validate(conversation)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Update conversation metadata.
    
    Allows updating conversation title, active status, and metadata.
    """
    try:
        conversation = await conversation_service.update_conversation(
            conversation_id,
            request,
            current_user.id
        )
        return ConversationResponse.model_validate(conversation)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation update failed"
        )


@router.delete("/{conversation_id}", response_model=BaseResponse)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Delete conversation and all messages.
    
    Permanently deletes the conversation and all associated messages.
    """
    try:
        success = await conversation_service.delete_conversation(
            conversation_id, 
            current_user.id
        )
        
        if success:
            return BaseResponse(
                success=True,
                message="Conversation deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation deletion failed"
        )


@router.get("/{conversation_id}/messages", response_model=PaginatedResponse[MessageResponse])
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get messages in a conversation.
    
    Returns paginated list of messages in the specified conversation.
    """
    try:
        messages, total = await conversation_service.get_messages(
            conversation_id,
            current_user.id,
            page=page,
            size=size
        )
        
        message_responses = [MessageResponse.model_validate(msg) for msg in messages]
        
        return PaginatedResponse.create(
            items=message_responses,
            total=total,
            page=page,
            size=size,
            message="Messages retrieved successfully"
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Send a message and get AI response.
    
    Sends a user message to the AI assistant and returns the response.
    Supports RAG (Retrieval-Augmented Generation) for context-aware responses
    and tool calling for enhanced functionality.
    """
    try:
        start_time = time.time()
        
        # Process chat request
        result = await conversation_service.process_chat(request, current_user.id)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        return ChatResponse(
            success=True,
            message="Chat response generated successfully",
            ai_message=result["ai_message"],
            conversation=result["conversation"],
            usage=result.get("usage"),
            rag_context=result.get("rag_context"),
            tool_calls_made=result.get("tool_calls_made"),
            response_time_ms=response_time_ms
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed"
        )


@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get conversation statistics for the current user.
    
    Returns statistics about the user's conversations and messages.
    """
    try:
        stats = await conversation_service.get_user_stats(current_user.id)
        return ConversationStats.model_validate(stats)
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation stats"
        )
