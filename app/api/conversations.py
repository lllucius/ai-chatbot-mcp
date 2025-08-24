"""Conversation and chat API endpoints."""

import json
import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.database import AsyncSessionLocal, get_db
from app.dependencies import (
    get_conversation_service,
    get_current_superuser,
    get_current_user,
)
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.conversation import ConversationService
from app.utils.api_errors import handle_api_errors, log_api_call
from app.utils.timestamp import utcnow
from shared.schemas.admin import RegistryStatsResponse
from shared.schemas.common import APIResponse, PaginatedResponse, PaginationParams
from shared.schemas.conversation import (
    ArchiveConversationsResult,
    ArchivePreviewItem,
    ArchivePreviewResponse,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationExportData,
    ConversationExportDataCSV,
    ConversationExportDataJSON,
    ConversationExportDataText,
    ConversationMetadata,
    ConversationResponse,
    ConversationSearchCriteria,
    ConversationSearchData,
    ConversationSearchMatchingMessage,
    ConversationSearchResult,
    ConversationSearchUserInfo,
    ConversationStats,
    ConversationStatsConversations,
    ConversationStatsData,
    ConversationStatsMessages,
    ConversationStatsRecentActivity,
    ConversationStatsUserEngagement,
    ConversationUpdate,
    ExportedMessage,
    ExportInfo,
    ImportConversationResult,
    MessageResponse,
    StreamCompleteResponse,
    StreamContentResponse,
    StreamEndResponse,
    StreamErrorResponse,
    StreamStartResponse,
    StreamToolCallResponse,
)

router = APIRouter(tags=["conversations"])


@router.post("/", response_model=APIResponse[ConversationResponse])
@handle_api_errors("Failed to create conversation")
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ConversationResponse]:
    """Create a new conversation."""
    log_api_call(
        "create_conversation", user_id=str(current_user.id), title=request.title
    )

    conversation = await conversation_service.create_conversation(
        request, current_user.id
    )
    payload = ConversationResponse.model_validate(conversation)
    return APIResponse[ConversationResponse](
        success=True,
        message="Conversation created successfully",
        data=payload,
    )


@router.get("/", response_model=APIResponse[PaginatedResponse[ConversationResponse]])
@handle_api_errors("Failed to retrieve conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[PaginatedResponse[ConversationResponse]]:
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

    payload = PaginatedResponse(
        items=conversation_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[ConversationResponse]](
        success=True,
        message="Conversations retrieved successfully",
        data=payload,
    )


@router.get("/byid/{conversation_id}", response_model=APIResponse[ConversationResponse])
@handle_api_errors("Failed to retrieve conversation")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ConversationResponse]:
    """Get conversation by ID."""
    log_api_call(
        "get_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    conversation = await conversation_service.get_conversation(
        conversation_id, current_user.id
    )
    payload = ConversationResponse.model_validate(conversation)
    return APIResponse[ConversationResponse](
        success=True,
        message="Conversation retrieved successfully",
        data=payload,
    )


@router.put("/byid/{conversation_id}", response_model=APIResponse[ConversationResponse])
@handle_api_errors("Failed to update conversation")
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ConversationResponse]:
    """Update conversation metadata and settings."""
    log_api_call(
        "update_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    conversation = await conversation_service.update_conversation(
        conversation_id, request, current_user.id
    )
    payload = ConversationResponse.model_validate(conversation)
    return APIResponse[ConversationResponse](
        success=True,
        message="Conversation updated successfully",
        data=payload,
    )


@router.delete("/byid/{conversation_id}", response_model=APIResponse)
@handle_api_errors("Failed to delete conversation")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse:
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
        return APIResponse(
            success=True,
            message="Conversation deleted successfully",
        )
    else:
        return APIResponse(
            success=False,
            message="Conversation not found",
            error={"code": "CONVERSATION_NOT_FOUND"},
        )


@router.get(
    "/{conversation_id}/messages",
)
@handle_api_errors("Failed to retrieve messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[PaginatedResponse[MessageResponse]]:
    """Get paginated messages from a conversation (alternative endpoint pattern)."""
    log_api_call(
        "get_conversation_messages",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
        page=page,
        size=size,
    )

    messages, total = await conversation_service.get_messages(
        conversation_id, current_user.id, page=page, size=size
    )

    message_responses = [MessageResponse.model_validate(msg) for msg in messages]

    payload = PaginatedResponse(
        items=message_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[MessageResponse]](
        success=True,
        message="Messages retrieved successfully",
        data=payload,
    )


@router.get(
    "/byid/{conversation_id}/messages",
    response_model=APIResponse[List[MessageResponse]],
)
@handle_api_errors("Failed to retrieve messages")
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[List[MessageResponse]]:
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

    payload = PaginatedResponse(
        items=message_responses,
        pagination=PaginationParams(
            total=total,
            page=page,
            per_page=size,
        ),
    )

    return APIResponse[PaginatedResponse[MessageResponse]](
        success=True,
        message="Messages retrieved successfully",
        data=payload,
    )

@router.post("/chat", response_model=APIResponse[ChatResponse])
@handle_api_errors("Chat processing failed")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ChatResponse]:
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

    response_time_ms = (time.time() - start_time) * 1000

    # Ensure all fields are well-typed
    ai_message = MessageResponse.model_validate(result["ai_message"])
    conversation = ConversationResponse.model_validate(result["conversation"])
    usage = result.get("usage")
    rag_context = result.get("rag_context")
    tool_calls_made = result.get("tool_calls_made")
    tool_call_summary = result.get("tool_call_summary")

    payload = ChatResponse(
        success=True,
        message="Chat response generated successfully with registry integration",
        ai_message=ai_message,
        conversation=conversation,
        usage=usage,
        rag_context=rag_context,
        tool_calls_made=tool_calls_made,
        tool_call_summary=tool_call_summary,
        response_time_ms=response_time_ms,
    )
    return APIResponse[ChatResponse](
        success=True,
        message="Chat response generated successfully",
        data=payload,
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
                        content_event = StreamContentResponse(
                            content=chunk.get("content", "")
                        )
                        yield f"data: {json.dumps(content_event.model_dump())}\n\n"
                    elif chunk.get("type") == "tool_call":
                        tool_event = StreamToolCallResponse(
                            tool=chunk.get("tool"), result=chunk.get("result")
                        )
                        yield f"data: {json.dumps(tool_event.model_dump())}\n\n"
                    elif chunk.get("type") == "complete":
                        response_data = chunk.get("response", {})

                        # Properly validate ai_message and conversation fields
                        for k, v in response_data.items():
                            if k == "ai_message":
                                response_data[k] = MessageResponse.model_validate(
                                    v
                                ).model_dump(mode="json")
                            elif k == "conversation":
                                response_data[k] = ConversationResponse.model_validate(
                                    v
                                ).model_dump(mode="json")
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
                                error_event = StreamErrorResponse(
                                    error=f"Unexpected key value: {k}"
                                )
                                yield f"data: {json.dumps(error_event.model_dump())}\n\n"
                        complete_event = StreamCompleteResponse(response=response_data)
                        yield f"data: {json.dumps(complete_event.model_dump())}\n\n"
                        break
                    elif chunk.get("type") == "error":
                        error_event = StreamErrorResponse(
                            error=chunk.get("error", "Unknown error")
                        )
                        yield f"data: {json.dumps(error_event.model_dump())}\n\n"
                        break
            except Exception as e:
                error_event = StreamErrorResponse(error=str(e))
                yield f"data: {json.dumps(error_event.model_dump())}\n\n"

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


@router.get("/stats", response_model=APIResponse[ConversationStats])
@handle_api_errors("Failed to retrieve conversation stats")
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ConversationStats]:
    """Get conversation statistics for the current user with registry insights.

    Returns statistics about the user's conversations and messages, plus
    insights from prompt and profile registries.
    """
    log_api_call("get_conversation_stats", user_id=str(current_user.id))

    stats = await conversation_service.get_user_stats(current_user.id)
    payload = ConversationStats.model_validate(stats)
    return APIResponse[ConversationStats](
        success=True,
        message="Conversation stats retrieved successfully",
        data=payload,
    )


@router.get("/registry-stats", response_model=APIResponse[RegistryStatsResponse])
@handle_api_errors("Failed to retrieve registry statistics")
async def get_registry_stats(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[RegistryStatsResponse]:
    """Get registry statistics showing prompt, profile, and tool usage.

    Returns comprehensive statistics about registry usage including:
    - Active prompts and most used prompts
    - Active LLM profiles and usage patterns
    - MCP tools and server status
    """
    log_api_call("get_registry_stats", user_id=str(current_user.id))

    registry_stats = await conversation_service._get_registry_stats()
    payload = RegistryStatsResponse(
        success=True,
        message="Registry statistics retrieved successfully",
        data=registry_stats,
    )
    return APIResponse[RegistryStatsResponse](
        success=True,
        message="Registry statistics retrieved successfully",
        data=payload,
    )


@router.get(
    "/byid/{conversation_id}/export",
    response_model=APIResponse[ConversationExportData],
)
@handle_api_errors("Failed to export conversation")
async def export_conversation(
    conversation_id: int,
    format: str = Query("json", description="Export format: json, txt, csv"),
    include_metadata: bool = Query(True, description="Include conversation metadata"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ConversationExportData]:
    """Export a conversation to various formats."""
    log_api_call(
        "export_conversation",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
        format=format,
    )

    # Get conversation with permission check
    conversation = await conversation_service.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise NotFoundError("Conversation not found")

    # Check permissions
    if conversation.user_id != current_user.id and not current_user.is_superuser:
        raise AuthorizationError("Access denied to this conversation")

    # Get messages
    messages_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )

    result = await db.execute(messages_query)
    messages = result.scalars().all()

    export_info = ExportInfo(
        format=format,
        exported_at=utcnow().isoformat(),
        message_count=len(messages),
        includes_metadata=include_metadata,
    )

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

        exported_messages = [
            ExportedMessage(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
                tool_calls=msg.tool_calls,
            )
            for msg in messages
        ]

        # Use empty metadata if not included
        if include_metadata and conversation_metadata:
            export_data_json = ConversationExportDataJSON(
                conversation=conversation_metadata,
                messages=exported_messages,
            )
        else:
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

        export_data_text = ConversationExportDataText(
            content=text_content,
            format="text",
        )

        response_payload = ConversationExportData(
            data=export_data_text,
            export_info=export_info,
        )

        return APIResponse[ConversationExportData](
            success=True,
            message="Conversation exported successfully in text format",
            data=response_payload,
        )

    elif format == "csv":
        csv_lines = []

        if include_metadata:
            csv_lines.append("# Conversation Export")
            csv_lines.append(f"# Title: {conversation.title}")
            csv_lines.append(f"# Created: {conversation.created_at.isoformat()}")
            csv_lines.append(f"# Messages: {len(messages)}")
            csv_lines.append("")

        csv_lines.append("timestamp,role,content,tool_calls,tool_call_id,name")

        for msg in messages:
            content = msg.content.replace('"', '""') if msg.content else ""
            tool_calls = json.dumps(msg.tool_calls) if msg.tool_calls else ""

            csv_lines.append(
                f'"{msg.created_at.isoformat()}","{msg.role}","{content}",'
                f'"{tool_calls}","{msg.tool_call_id or ""}","{msg.name or ""}"'
            )

        csv_content = "\n".join(csv_lines)

        export_data_csv = ConversationExportDataCSV(
            content=csv_content,
            format="csv",
        )

        response_payload = ConversationExportData(
            data=export_data_csv,
            export_info=export_info,
        )

        return APIResponse[ConversationExportData](
            success=True,
            message="Conversation exported successfully in CSV format",
            data=response_payload,
        )

    else:
        raise ValidationError("Invalid export format. Use: json, txt, or csv")


@router.post(
    "/import", response_model=APIResponse[ImportConversationResult]
)
@handle_api_errors("Failed to import conversation")
async def import_conversation(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Override conversation title"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> APIResponse[ImportConversationResult]:
    """Import a conversation from a JSON file."""
    log_api_call("import_conversation", user_id=str(current_user.id))

    try:
        # Validate file type
        if not file.filename.endswith(".json"):
            raise ValidationError("Only JSON files are supported for import")

        # Read and parse file
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")

        # Validate data structure
        if "messages" not in data:
            raise ValidationError("Invalid conversation format: missing 'messages' field")

        # Extract conversation info
        conversation_data = data.get("conversation", {})
        messages_data = data["messages"]

        if not messages_data:
            raise ValidationError("No messages found in import file")

        # Create new conversation
        conv_title = title or conversation_data.get(
            "title",
            f"Imported conversation {utcnow().strftime('%Y-%m-%d %H:%M')}",
        )

        conversation_create = ConversationCreate(title=conv_title)

        new_conversation = await conversation_service.create_conversation(
            conversation_create, current_user
        )

        # Import messages
        imported_count = 0
        errors = []

        for msg_data in messages_data:
            try:
                required_fields = ["role", "content"]
                missing_field = next(
                    (field for field in required_fields if field not in msg_data), None
                )
                if missing_field:
                    errors.append(f"Message missing required field: {missing_field}")
                    continue

                message = Message(
                    conversation_id=new_conversation.id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    tool_calls=msg_data.get("tool_calls"),
                    tool_call_id=msg_data.get("tool_call_id"),
                    name=msg_data.get("name"),
                )

                conversation_service.db.add(message)
                imported_count += 1

            except Exception as e:
                errors.append(f"Failed to import message: {str(e)}")

        await conversation_service.db.commit()

        result = ImportConversationResult(
            conversation_id=str(new_conversation.id),
            conversation_title=conv_title,
            imported_messages=imported_count,
            total_messages=len(messages_data),
            errors=errors[:5],
        )

        return APIResponse[ImportConversationResult](
            success=True,
            message=f"Conversation imported successfully with {imported_count} messages",
            data=result,
        )

    except Exception:
        await conversation_service.db.rollback()
        raise


@router.post(
    "/archive",
    response_model=APIResponse[ArchivePreviewResponse | ArchiveConversationsResult],
)
@handle_api_errors("Failed to archive conversations")
async def archive_conversations(
    older_than_days: int = Query(
        90, ge=1, le=365, description="Archive conversations older than X days"
    ),
    inactive_only: bool = Query(
        True, description="Archive only inactive conversations"
    ),
    dry_run: bool = Query(
        True, description="Perform dry run without actually archiving"
    ),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ArchivePreviewResponse | ArchiveConversationsResult]:
    """Archive old conversations by marking them as inactive."""
    log_api_call(
        "archive_conversations",
        user_id=str(current_user.id),
        older_than_days=older_than_days,
        inactive_only=inactive_only,
        dry_run=dry_run,
    )

    try:
        cutoff_date = utcnow() - timedelta(days=older_than_days)
        query = select(Conversation).where(Conversation.created_at < cutoff_date)

        if inactive_only:
            query = query.where(Conversation.is_active.is_(False))
        else:
            query = query.where(Conversation.is_active.is_(True))

        result = await db.execute(query)
        conversations = result.scalars().all()

        criteria = {
            "older_than_days": older_than_days,
            "inactive_only": inactive_only,
            "cutoff_date": cutoff_date.isoformat(),
        }

        if dry_run:
            preview_items = []
            for conv in conversations[:10]:
                msg_count = await db.scalar(
                    select(func.count(Message.id)).where(
                        Message.conversation_id == conv.id
                    )
                )
                preview_items.append(
                    ArchivePreviewItem(
                        id=str(conv.id),
                        title=conv.title,
                        created_at=conv.created_at.isoformat(),
                        is_active=conv.is_active,
                        message_count=msg_count or 0,
                    )
                )

            preview = ArchivePreviewResponse(
                total_count=len(conversations),
                preview=preview_items,
                criteria=criteria,
            )

            return APIResponse[ArchivePreviewResponse](
                success=True,
                message=f"Dry run: {len(conversations)} conversations would be archived",
                data=preview,
            )
        else:
            archived_count = 0
            for conv in conversations:
                conv.is_active = False
                archived_count += 1

            await db.commit()

            result = ArchiveConversationsResult(
                archived_count=archived_count,
                criteria=criteria,
            )

            return APIResponse[ArchiveConversationsResult](
                success=True,
                message=f"Archived {archived_count} conversations successfully",
                data=result,
            )

    except Exception:
        await db.rollback()
        raise


@router.get("/search", response_model=APIResponse[ConversationSearchData])
@handle_api_errors("Failed to search conversations")
async def search_conversations_and_messages(
    query: str = Query(..., description="Search query"),
    search_messages: bool = Query(True, description="Search within message content"),
    user_filter: Optional[str] = Query(None, description="Username to filter by"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    active_only: bool = Query(True, description="Search only active conversations"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ConversationSearchData]:
    """Search conversations and messages with advanced filtering options."""
    log_api_call("search_conversations", user_id=str(current_user.id), query=query)

    try:
        base_query = select(Conversation).join(User, Conversation.user_id == User.id)

        if not current_user.is_superuser:
            base_query = base_query.where(Conversation.user_id == current_user.id)

        filters = []
        title_filter = Conversation.title.ilike(f"%{query}%")
        search_filters = [title_filter]

        if search_messages:
            message_subquery = (
                select(Message.conversation_id)
                .where(Message.content.ilike(f"%{query}%"))
                .distinct()
            )
            message_filter = Conversation.id.in_(message_subquery)
            search_filters.append(message_filter)

        filters.append(or_(*search_filters))

        if user_filter:
            filters.append(User.username.ilike(f"%{user_filter}%"))
        if active_only:
            filters.append(Conversation.is_active.is_(True))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                filters.append(Conversation.created_at >= date_from_obj)
            except ValueError:
                raise ValidationError("Invalid date_from format. Use YYYY-MM-DD")
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                filters.append(Conversation.created_at < date_to_obj)
            except ValueError:
                raise ValidationError("Invalid date_to format. Use YYYY-MM-DD")

        if filters:
            base_query = base_query.where(and_(*filters))
        base_query = base_query.order_by(Conversation.updated_at.desc()).limit(limit)

        result = await db.execute(base_query)
        conversations = result.scalars().all()

        search_results: List[ConversationSearchResult] = []
        for conv in conversations:
            user_result = await db.execute(select(User).where(User.id == conv.user_id))
            user = user_result.scalar_one_or_none()
            msg_count = await db.scalar(
                select(func.count(Message.id)).where(Message.conversation_id == conv.id)
            )

            matching_messages: List[ConversationSearchMatchingMessage] = []
            if search_messages:
                message_query = (
                    select(Message)
                    .where(
                        and_(
                            Message.conversation_id == conv.id,
                            Message.content.ilike(f"%{query}%"),
                        )
                    )
                    .order_by(Message.created_at)
                    .limit(3)
                )
                msg_result = await db.execute(message_query)
                messages = msg_result.scalars().all()
                for msg in messages:
                    content = msg.content
                    excerpt = ""
                    if query.lower() in content.lower():
                        pos = content.lower().find(query.lower())
                        start = max(0, pos - 50)
                        end = min(len(content), pos + len(query) + 50)
                        excerpt = content[start:end]
                        if start > 0:
                            excerpt = "..." + excerpt
                        if end < len(content):
                            excerpt = excerpt + "..."
                    else:
                        excerpt = content[:100] + ("..." if len(content) > 100 else "")

                    matching_messages.append(
                        ConversationSearchMatchingMessage(
                            id=str(msg.id),
                            role=msg.role,
                            excerpt=excerpt,
                            created_at=msg.created_at.isoformat(),
                        )
                    )

            search_results.append(
                ConversationSearchResult(
                    id=str(conv.id),
                    title=conv.title,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
                    is_active=conv.is_active,
                    message_count=msg_count or 0,
                    user=ConversationSearchUserInfo(
                        username=user.username if user else "Unknown",
                        email=user.email if user else "Unknown",
                    ),
                    matching_messages=matching_messages,
                )
            )

        criteria = ConversationSearchCriteria(
            query=query,
            search_messages=search_messages,
            user_filter=user_filter,
            date_from=date_from,
            date_to=date_to,
            active_only=active_only,
            limit=limit,
        )

        payload = ConversationSearchData(
            results=search_results,
            total_found=len(search_results),
            search_criteria=criteria,
            timestamp=utcnow().isoformat(),
        )

        return APIResponse[ConversationSearchData](
            success=True,
            message="Search completed",
            data=payload,
        )

    except Exception:
        raise


@router.get("/stats", response_model=APIResponse[ConversationStatsData])
@handle_api_errors("Failed to get conversation statistics")
async def get_conversation_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ConversationStatsData]:
    """Get comprehensive conversation statistics and analytics."""
    log_api_call("get_conversation_statistics", user_id=str(current_user.id))

    try:
        total_conversations = await db.scalar(select(func.count(Conversation.id)))
        active_conversations = await db.scalar(
            select(func.count(Conversation.id)).where(Conversation.is_active.is_(True))
        )
        total_messages = await db.scalar(select(func.count(Message.id)))
        avg_messages = (
            await db.scalar(
                select(func.avg(func.count(Message.id)))
                .select_from(Message)
                .group_by(Message.conversation_id)
            )
            or 0
        )
        seven_days_ago = utcnow() - timedelta(days=7)
        recent_conversations = (
            await db.scalar(
                select(func.count(Conversation.id)).where(
                    Conversation.created_at >= seven_days_ago
                )
            )
            or 0
        )
        recent_messages = (
            await db.scalar(
                select(func.count(Message.id)).where(
                    Message.created_at >= seven_days_ago
                )
            )
            or 0
        )
        users_with_conversations = (
            await db.scalar(select(func.count(func.distinct(Conversation.user_id))))
            or 0
        )

        top_users_query = (
            select(
                User.username,
                func.count(Conversation.id).label("conversation_count"),
                func.sum(
                    select(func.count(Message.id))
                    .where(Message.conversation_id == Conversation.id)
                    .scalar_subquery()
                ).label("total_messages"),
            )
            .join(User, Conversation.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(func.count(Conversation.id).desc())
            .limit(5)
        )
        top_users = await db.execute(top_users_query)
        top_users_list = [
            {
                "username": row.username,
                "conversation_count": row.conversation_count,
                "total_messages": row.total_messages or 0,
            }
            for row in top_users.fetchall()
        ]

        role_stats_query = select(
            Message.role, func.count(Message.id).label("count")
        ).group_by(Message.role)
        role_stats = await db.execute(role_stats_query)
        role_distribution = {row.role: row.count for row in role_stats.fetchall()}

        payload = ConversationStatsData(
            conversations=ConversationStatsConversations(
                total=total_conversations or 0,
                active=active_conversations or 0,
                inactive=(total_conversations or 0) - (active_conversations or 0),
            ),
            messages=ConversationStatsMessages(
                total=total_messages or 0,
                avg_per_conversation=round(avg_messages, 2),
                role_distribution=role_distribution,
            ),
            recent_activity=ConversationStatsRecentActivity(
                conversations_last_7_days=recent_conversations,
                messages_last_7_days=recent_messages,
            ),
            user_engagement=ConversationStatsUserEngagement(
                users_with_conversations=users_with_conversations,
                top_users=top_users_list,
            ),
            timestamp=utcnow().isoformat(),
        )

        return APIResponse[ConversationStatsData](
            success=True,
            message="Conversation statistics retrieved successfully",
            data=payload,
        )
    except Exception:
        raise
