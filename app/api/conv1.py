"""Conversation and chat API endpoints."""

import json
import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.admin_responses import (
    ConversationStatsResponse,
    RegistryStatsResponse,
    SearchResponse,
)
from shared.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)
from shared.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationStats,
    ConversationUpdate,
    MessageResponse,
    StreamCompleteResponse,
    StreamContentResponse,
    StreamEndResponse,
    StreamErrorResponse,
    StreamStartResponse,
    StreamToolCallResponse,
)
from shared.schemas.conversation_responses import (
    ConversationExportData,
    ConversationExportDataCSV,
    ConversationExportDataJSON,
    ConversationExportDataText,
    ConversationMetadata,
    ExportedMessage,
    ExportInfo,
)

from ..database import AsyncSessionLocal, get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.conversation import Conversation, Message
from ..models.user import User
from ..services.conversation import ConversationService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["conversations"])


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Get conversation service instance with database session."""
    return ConversationService(db)


@router.post("/", response_model=ConversationResponse)
@handle_api_errors("Failed to create conversation")
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    log_api_call(
        "create_conversation", user_id=str(current_user.id), title=request.title
    )

    conversation = await conversation_service.create_conversation(
        request, current_user.id
    )
    return ConversationResponse.model_validate(conversation)


@router.get("/", response_model=PaginatedResponse[ConversationResponse])
@handle_api_errors("Failed to retrieve conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """List user's conversations with pagination and filtering."""
    log_api_call(
        "list_conversations",
        user_id=str(current_user.id),
        page=page,
        size=size,
        active_only=active_only,
    )

    conversations, total = await conversation_service.list_conversations(
        user_id=current_user.id, page=page, size=size, active_only=active_only
    )

    conversation_responses = [
        ConversationResponse.model_validate(conv) for conv in conversations
    ]

    return PaginatedResponse.create(
        items=conversation_responses,
        page=page,
        size=size,
        total=total,
        message="Conversations retrieved successfully",
    )


@router.get("/byid/{conversation_id}", response_model=ConversationResponse)
@handle_api_errors("Failed to retrieve conversation")
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get conversation by ID."""
    log_api_call(
        "get_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    conversation = await conversation_service.get_conversation(
        conversation_id, current_user.id
    )
    return ConversationResponse.model_validate(conversation)


@router.put("/byid/{conversation_id}", response_model=ConversationResponse)
@handle_api_errors("Failed to update conversation")
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Update conversation metadata and settings."""
    log_api_call(
        "update_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    conversation = await conversation_service.update_conversation(
        conversation_id, request, current_user.id
    )
    return ConversationResponse.model_validate(conversation)


@router.delete("/byid/{conversation_id}", response_model=APIResponse)
@handle_api_errors("Failed to delete conversation")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Delete conversation and all associated messages."""
    log_api_call(
        "delete_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    success = await conversation_service.delete_conversation(
        conversation_id, current_user.id
    )

    if success:
        return SuccessResponse.create(message="Conversation deleted successfully")
    else:
        return ErrorResponse.create(
            error_code="CONVERSATION_NOT_FOUND",
            message="Conversation not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get(
    "/byid/{conversation_id}/messages",
    response_model=PaginatedResponse[MessageResponse],
)
@handle_api_errors("Failed to retrieve messages")
async def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get paginated messages from a conversation."""
    log_api_call(
        "get_messages",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
        page=page,
        size=size,
    )

    messages, total = await conversation_service.get_messages(
        conversation_id, current_user.id, page=page, size=size
    )

    message_responses = [MessageResponse.model_validate(msg) for msg in messages]

    return PaginatedResponse.create(
        items=message_responses,
        page=page,
        size=size,
        total=total,
        message="Messages retrieved successfully",
    )


@router.post("/chat", response_model=ChatResponse)
@handle_api_errors("Chat processing failed")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Send a message and get AI response."""
    log_api_call(
        "chat",
        user_id=str(current_user.id),
        conversation_id=str(request.conversation_id),
        message_length=len(request.user_message),
    )

    start_time = time.time()

    # Process chat request with enhanced registry integration
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


@router.post("/chat/stream")
@handle_api_errors("Failed to process streaming chat request")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> StreamingResponse:
    """Send a message and get a streaming AI response."""
    log_api_call(
        "chat_stream",
        user_id=str(current_user.id),
        conversation_id=str(request.conversation_id),
        message_length=len(request.user_message),
    )

    async def generate_response():
        async with AsyncSessionLocal() as db:
            conversation_service = ConversationService(db)

            # Send initial event
            start_event = StreamStartResponse(message="Generating response...")
            yield f"data: {json.dumps(start_event.model_dump())}\n\n"

            try:
                # Process chat request with streaming
                async for chunk in conversation_service.process_chat_stream(
                    request, current_user.id
                ):
                    if chunk.get("type") == "content":
                        # Stream content chunks
                        content_event = StreamContentResponse(
                            content=chunk.get("content", "")
                        )
                        yield f"data: {json.dumps(content_event.model_dump())}\n\n"
                    elif chunk.get("type") == "tool_call":
                        # Stream tool call information
                        tool_event = StreamToolCallResponse(
                            tool=chunk.get("tool"), result=chunk.get("result")
                        )
                        yield f"data: {json.dumps(tool_event.model_dump())}\n\n"
                    elif chunk.get("type") == "complete":
                        # Send completion event with full response
                        response_data = chunk.get("response", {})
                        for k, v in response_data.items():
                            if k in ("ai_message", "conversation"):
                                response_data[k] = v.model_dump(mode="json")
                            elif k == "rag_context":
                                if v:
                                    ctx = []
                                    for item in v:
                                        item["chunk_id"] = str(item["chunk_id"])
                                        ctx.append(item)
                                    response_data[k] = json.dumps(ctx)
                                else:
                                    response_data[k] = {}
                            elif k == "tool_call_summary":
                                if v:
                                    response_data[k] = json.dumps(v)
                                else:
                                    response_data[k] = {}
                            else:
                                e = f"Unexpected key value: {k}"
                                error_event = StreamErrorResponse(error=str(e))
                                yield f"data: {json.dumps(error_event.model_dump())}\n\n"
                        complete_event = StreamCompleteResponse(response=response_data)
                        yield f"data: {json.dumps(complete_event.model_dump())}\n\n"
                        break
                    elif chunk.get("type") == "error":
                        # Send error event
                        error_event = StreamErrorResponse(
                            error=chunk.get("error", "Unknown error")
                        )
                        yield f"data: {json.dumps(error_event.model_dump())}\n\n"
                        break
            except Exception as e:
                # Send error event for any unhandled exceptions
                error_event = StreamErrorResponse(error=str(e))
                yield f"data: {json.dumps(error_event.model_dump())}\n\n"

            # Send end event
            end_event = StreamEndResponse()
            yield f"data: {json.dumps(end_event.model_dump())}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/stats", response_model=ConversationStats)
@handle_api_errors("Failed to retrieve conversation stats")
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get conversation statistics for the current user with registry insights.

    Returns statistics about the user's conversations and messages, plus
    insights from prompt and profile registries.
    """
    log_api_call("get_conversation_stats", user_id=str(current_user.id))

    stats = await conversation_service.get_user_stats(current_user.id)
    return ConversationStats.model_validate(stats)


@router.get("/registry-stats", response_model=RegistryStatsResponse)
@handle_api_errors("Failed to retrieve registry statistics")
async def get_registry_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> RegistryStatsResponse:
    """
    Get registry statistics showing prompt, profile, and tool usage.

    Returns comprehensive statistics about registry usage including:
    - Active prompts and most used prompts
    - Active LLM profiles and usage patterns
    - MCP tools and server status
    """
    log_api_call("get_registry_stats", user_id=str(current_user.id))

    registry_stats = await conversation_service._get_registry_stats()

    return RegistryStatsResponse(
        success=True,
        message="Registry statistics retrieved successfully",
        data=registry_stats,
    )


@router.get(
    "/conversations/byid/{conversation_id}/export",
    response_model=APIResponse[ConversationExportData],
)
@handle_api_errors("Failed to export conversation")
async def export_conversation(
    conversation_id: UUID,
    format: str = Query("json", description="Export format: json, txt, csv"),
    include_metadata: bool = Query(True, description="Include conversation metadata"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
    db: AsyncSession = Depends(get_db),
):
    """Export a conversation to various formats."""
    log_api_call(
        "export_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
        format=format,
    )

    try:
        # Get conversation with permission check
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Check permissions
        if conversation.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation",
            )

        # Get messages
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )

        result = await db.execute(messages_query)
        messages = result.scalars().all()

        # Export data based on format
        if format == "json":
            # Create conversation metadata if requested
            conversation_metadata = None
            if include_metadata:
                conversation_metadata = ConversationMetadata(
                    id=str(conversation.id),
                    title=conversation.title,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=(
                        conversation.updated_at.isoformat()
                        if conversation.updated_at
                        else None
                    ),
                    is_active=conversation.is_active,
                    message_count=len(messages),
                )

            # Create exported messages
            exported_messages = []
            for msg in messages:
                exported_message = ExportedMessage(
                    id=str(msg.id),
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at.isoformat(),
                    tool_calls=msg.tool_calls,
                    tool_call_id=msg.tool_call_id,
                    name=msg.name,
                )
                exported_messages.append(exported_message)

            # Create the export data structure using proper ConversationExportDataJSON
            if include_metadata and conversation_metadata:
                export_data_json = ConversationExportDataJSON(
                    conversation=conversation_metadata,
                    messages=exported_messages,
                )
            else:
                # Create empty conversation metadata for consistency
                empty_metadata = ConversationMetadata(
                    id=str(conversation.id),
                    title=conversation.title,
                    created_at=conversation.created_at.isoformat(),
                    updated_at=(
                        conversation.updated_at.isoformat()
                        if conversation.updated_at
                        else None
                    ),
                    is_active=conversation.is_active,
                    message_count=len(messages),
                )
                export_data_json = ConversationExportDataJSON(
                    conversation=empty_metadata,
                    messages=exported_messages,
                )

            export_info = ExportInfo(
                format=format,
                exported_at=datetime.utcnow().isoformat(),
                message_count=len(messages),
                includes_metadata=include_metadata,
            )

            response_payload = ConversationExportData(
                data=export_data_json,
                export_info=export_info,
            )

            return APIResponse[ConversationExportData](
                success=True,
                message="Conversation exported successfully in JSON format",
                data=response_payload,
            )

        elif format == "txt":
            # Plain text format
            lines = []

            if include_metadata:
                lines.append(f"Conversation: {conversation.title}")
                lines.append(
                    f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                lines.append(f"Messages: {len(messages)}")
                lines.append("-" * 50)
                lines.append("")

            for msg in messages:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] {msg.role.upper()}: {msg.content}")
                lines.append("")

            text_content = "\n".join(lines)

            # Create properly structured text export data
            export_data_text = ConversationExportDataText(
                content=text_content,
                format="text",
            )

            export_info = ExportInfo(
                format=format,
                exported_at=datetime.utcnow().isoformat(),
                message_count=len(messages),
                includes_metadata=include_metadata,
            )

            return APIResponse[ConversationExportData](
                success=True,
                message="Conversation exported successfully in text format",
                data=ConversationExportData(
                    data=export_data_text,
                    export_info=export_info,
                ),
            )

        elif format == "csv":
            # CSV format
            csv_lines = []

            if include_metadata:
                csv_lines.append("# Conversation Export")
                csv_lines.append(f"# Title: {conversation.title}")
                csv_lines.append(f"# Created: {conversation.created_at.isoformat()}")
                csv_lines.append(f"# Messages: {len(messages)}")
                csv_lines.append("")

            # CSV header
            csv_lines.append("timestamp,role,content,tool_calls,tool_call_id,name")

            for msg in messages:
                # Escape CSV content
                content = msg.content.replace('"', '""') if msg.content else ""
                tool_calls = json.dumps(msg.tool_calls) if msg.tool_calls else ""

                csv_lines.append(
                    f'"{msg.created_at.isoformat()}","{msg.role}","{content}",'
                    f'"{tool_calls}","{msg.tool_call_id or ""}","{msg.name or ""}"'
                )

            csv_content = "\n".join(csv_lines)

            # Create properly structured CSV export data
            export_data_csv = ConversationExportDataCSV(
                content=csv_content,
                format="csv",
            )

            export_info = ExportInfo(
                format=format,
                exported_at=datetime.utcnow().isoformat(),
                message_count=len(messages),
                includes_metadata=include_metadata,
            )

            return APIResponse[ConversationExportData](
                success=True,
                message="Conversation exported successfully in CSV format",
                data=ConversationExportData(
                    data=export_data_csv,
                    export_info=export_info,
                ),
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Use: json, txt, or csv",
            )

    except HTTPException:
        raise
    except Exception:
        raise


