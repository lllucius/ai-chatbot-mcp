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

@router.post("/conversations/import", response_model=APIResponse)
@handle_api_errors("Failed to import conversation")
async def import_conversation(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Override conversation title"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Import a conversation from a JSON file."""
    log_api_call("import_conversation", user_id=str(current_user.id))

    try:
        # Validate file type
        if not file.filename.endswith(".json"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON files are supported for import",
            )

        # Read and parse file
        content = await file.read()
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}",
            )

        # Validate data structure
        if "messages" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation format: missing 'messages' field",
            )

        # Extract conversation info
        conversation_data = data.get("conversation", {})
        messages_data = data["messages"]

        if not messages_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages found in import file",
            )

        # Create new conversation
        conv_title = title or conversation_data.get(
            "title",
            f"Imported conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        )

        from shared.schemas.conversation import ConversationCreate

        conversation_create = ConversationCreate(title=conv_title)

        new_conversation = await conversation_service.create_conversation(
            conversation_create, current_user
        )

        # Import messages
        imported_count = 0
        errors = []

        for msg_data in messages_data:
            try:
                # Validate message structure
                required_fields = ["role", "content"]
                for field in required_fields:
                    if field not in msg_data:
                        errors.append(f"Message missing required field: {field}")
                        continue

                # Create message
                from ..models.conversation import Message

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

        return SuccessResponse.create(
            data={
                "conversation_id": str(new_conversation.id),
                "conversation_title": conv_title,
                "imported_messages": imported_count,
                "total_messages": len(messages_data),
                "errors": errors[:5],  # Limit error reporting
            },
            message=f"Conversation imported successfully with {imported_count} messages"
        )

    except HTTPException:
        raise
    except Exception:
        await conversation_service.db.rollback()
        raise


@router.post("/conversations/archive", response_model=APIResponse)
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
):
    """Archive old conversations by marking them as inactive."""
    log_api_call(
        "archive_conversations",
        user_id=str(current_user.id),
        older_than_days=older_than_days,
        inactive_only=inactive_only,
        dry_run=dry_run,
    )

    try:
        # Build query
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        query = select(Conversation).where(Conversation.created_at < cutoff_date)

        if inactive_only:
            query = query.where(Conversation.is_active is False)
        else:
            query = query.where(Conversation.is_active is True)

        # Get conversations to archive
        result = await db.execute(query)
        conversations = result.scalars().all()

        if dry_run:
            # Return preview
            preview = []
            for conv in conversations[:10]:  # Limit preview
                # Get message count
                msg_count = await db.scalar(
                    select(func.count(Message.id)).where(
                        Message.conversation_id == conv.id
                    )
                )

                preview.append(
                    {
                        "id": str(conv.id),
                        "title": conv.title,
                        "created_at": conv.created_at.isoformat(),
                        "is_active": conv.is_active,
                        "message_count": msg_count or 0,
                    }
                )

            return SuccessResponse.create(
                data={
                    "total_count": len(conversations),
                    "preview": preview,
                    "criteria": {
                        "older_than_days": older_than_days,
                        "inactive_only": inactive_only,
                        "cutoff_date": cutoff_date.isoformat(),
                    },
                },
                message=f"Dry run: {len(conversations)} conversations would be archived"
            )
        else:
            # Actually archive conversations
            archived_count = 0

            for conv in conversations:
                conv.is_active = False
                archived_count += 1

            await db.commit()

            return SuccessResponse.create(
                data={
                    "archived_count": archived_count,
                    "criteria": {
                        "older_than_days": older_than_days,
                        "inactive_only": inactive_only,
                        "cutoff_date": cutoff_date.isoformat(),
                    },
                },
                message=f"Archived {archived_count} conversations successfully"
            )

    except Exception:
        await db.rollback()
        raise


@router.get("/conversations/search", response_model=SearchResponse)
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
):
    """Search conversations and messages with advanced filtering options."""
    log_api_call("search_conversations", user_id=str(current_user.id), query=query)

    try:
        # Build base query
        base_query = select(Conversation).join(User, Conversation.user_id == User.id)

        # Permission check for non-superusers
        if not current_user.is_superuser:
            base_query = base_query.where(Conversation.user_id == current_user.id)

        # Build filters
        filters = []

        # Text search in conversation titles
        title_filter = Conversation.title.ilike(f"%{query}%")
        search_filters = [title_filter]

        # Search in message content if requested
        if search_messages:
            # Subquery for conversations with matching messages
            message_subquery = (
                select(Message.conversation_id)
                .where(Message.content.ilike(f"%{query}%"))
                .distinct()
            )

            message_filter = Conversation.id.in_(message_subquery)
            search_filters.append(message_filter)

        filters.append(or_(*search_filters))

        # User filter
        if user_filter:
            filters.append(User.username.ilike(f"%{user_filter}%"))

        # Active conversations only
        if active_only:
            filters.append(Conversation.is_active is True)

        # Date range filters
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                filters.append(Conversation.created_at >= date_from_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD",
                )

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                filters.append(Conversation.created_at < date_to_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD",
                )

        # Apply filters
        if filters:
            base_query = base_query.where(and_(*filters))

        # Add ordering and limit
        base_query = base_query.order_by(Conversation.updated_at.desc()).limit(limit)

        # Execute query
        result = await db.execute(base_query)
        conversations = result.scalars().all()

        # Format results with message context
        results = []
        for conv in conversations:
            # Get user info
            user_result = await db.execute(select(User).where(User.id == conv.user_id))
            user = user_result.scalar_one_or_none()

            # Get message count
            msg_count = await db.scalar(
                select(func.count(Message.id)).where(Message.conversation_id == conv.id)
            )

            # Get matching messages if searching content
            matching_messages = []
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
                    .limit(3)  # Limit to 3 matching messages per conversation
                )

                msg_result = await db.execute(message_query)
                messages = msg_result.scalars().all()

                for msg in messages:
                    # Highlight matching text (simple approach)
                    content = msg.content
                    if query.lower() in content.lower():
                        # Find the position and create excerpt
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
                        {
                            "id": str(msg.id),
                            "role": msg.role,
                            "excerpt": excerpt,
                            "created_at": msg.created_at.isoformat(),
                        }
                    )

            results.append(
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": (
                        conv.updated_at.isoformat() if conv.updated_at else None
                    ),
                    "is_active": conv.is_active,
                    "message_count": msg_count or 0,
                    "user": {
                        "username": user.username if user else "Unknown",
                        "email": user.email if user else "Unknown",
                    },
                    "matching_messages": matching_messages,
                }
            )

        return SearchResponse(
            success=True,
            data={
                "results": results,
                "total_found": len(results),
                "search_criteria": {
                    "query": query,
                    "search_messages": search_messages,
                    "user_filter": user_filter,
                    "date_from": date_from,
                    "date_to": date_to,
                    "active_only": active_only,
                    "limit": limit,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception:
        raise


@router.get("/conversations/stats", response_model=ConversationStatsResponse)
@handle_api_errors("Failed to get conversation statistics")
async def get_conversation_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationStatsResponse:
    """Get comprehensive conversation statistics and analytics."""
    log_api_call("get_conversation_statistics", user_id=str(current_user.id))

    try:
        # Basic conversation counts
        total_conversations = await db.scalar(select(func.count(Conversation.id)))
        active_conversations = await db.scalar(
            select(func.count(Conversation.id)).where(Conversation.is_active is True)
        )

        # Message statistics
        total_messages = await db.scalar(select(func.count(Message.id)))

        # Average messages per conversation
        avg_messages = (
            await db.scalar(
                select(func.avg(func.count(Message.id)))
                .select_from(Message)
                .group_by(Message.conversation_id)
            )
            or 0
        )

        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
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

        # User engagement
        users_with_conversations = (
            await db.scalar(select(func.count(func.distinct(Conversation.user_id))))
            or 0
        )

        # Top active users by conversation count
        top_users = await db.execute(
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

        top_users_list = []
        for row in top_users.fetchall():
            top_users_list.append(
                {
                    "username": row.username,
                    "conversation_count": row.conversation_count,
                    "total_messages": row.total_messages or 0,
                }
            )

        # Message role distribution
        role_stats = await db.execute(
            select(Message.role, func.count(Message.id).label("count")).group_by(
                Message.role
            )
        )

        role_distribution = {}
        for row in role_stats.fetchall():
            role_distribution[row.role] = row.count

        return ConversationStatsResponse(
            success=True,
            data={
                "conversations": {
                    "total": total_conversations or 0,
                    "active": active_conversations or 0,
                    "inactive": (total_conversations or 0)
                    - (active_conversations or 0),
                },
                "messages": {
                    "total": total_messages or 0,
                    "avg_per_conversation": round(avg_messages, 2),
                    "role_distribution": role_distribution,
                },
                "recent_activity": {
                    "conversations_last_7_days": recent_conversations,
                    "messages_last_7_days": recent_messages,
                },
                "user_engagement": {
                    "users_with_conversations": users_with_conversations,
                    "top_users": top_users_list,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        raise
