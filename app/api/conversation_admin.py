"""
Extended conversation management API endpoints.

This module provides additional conversation management endpoints that extend
the base conversation API with import/export, archival, and search operations.

Key Features:
- Conversation import/export operations
- Conversation archival and cleanup
- Advanced search across conversations and messages
- Conversation statistics and analytics
- Bulk conversation operations

"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.conversation import Conversation, Message
from ..models.user import User
from ..schemas.common import BaseResponse
from ..services.conversation import ConversationService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["conversation-admin"])


async def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Get conversation service instance."""
    return ConversationService(db)


@router.get("/conversations/{conversation_id}/export", response_model=Dict[str, Any])
@handle_api_errors("Failed to export conversation")
async def export_conversation(
    conversation_id: UUID,
    format: str = Query("json", description="Export format: json, txt, csv"),
    include_metadata: bool = Query(True, description="Include conversation metadata"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a conversation to various formats.
    
    Supports multiple export formats with optional metadata inclusion.
    Users can only export their own conversations unless they are superusers.
    
    Args:
        conversation_id: ID of the conversation to export
        format: Export format (json, txt, csv)
        include_metadata: Whether to include conversation metadata
    """
    log_api_call("export_conversation", user_id=str(current_user.id), 
                conversation_id=str(conversation_id), format=format)
    
    try:
        # Get conversation with permission check
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check permissions
        if conversation.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
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
            export_data = {
                "conversation": {
                    "id": str(conversation.id),
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                    "is_active": conversation.is_active,
                    "message_count": len(messages)
                } if include_metadata else {},
                "messages": []
            }
            
            for msg in messages:
                message_data = {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name
                }
                export_data["messages"].append(message_data)
            
            return {
                "success": True,
                "data": export_data,
                "export_info": {
                    "format": format,
                    "exported_at": datetime.utcnow().isoformat(),
                    "message_count": len(messages),
                    "includes_metadata": include_metadata
                }
            }
        
        elif format == "txt":
            # Plain text format
            lines = []
            
            if include_metadata:
                lines.append(f"Conversation: {conversation.title}")
                lines.append(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"Messages: {len(messages)}")
                lines.append("-" * 50)
                lines.append("")
            
            for msg in messages:
                timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"[{timestamp}] {msg.role.upper()}: {msg.content}")
                lines.append("")
            
            text_content = "\n".join(lines)
            
            return {
                "success": True,
                "data": {
                    "content": text_content,
                    "format": "text"
                },
                "export_info": {
                    "format": format,
                    "exported_at": datetime.utcnow().isoformat(),
                    "message_count": len(messages),
                    "includes_metadata": include_metadata
                }
            }
        
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
            
            return {
                "success": True,
                "data": {
                    "content": csv_content,
                    "format": "csv"
                },
                "export_info": {
                    "format": format,
                    "exported_at": datetime.utcnow().isoformat(),
                    "message_count": len(messages),
                    "includes_metadata": include_metadata
                }
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Use: json, txt, or csv"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/conversations/import", response_model=BaseResponse)
@handle_api_errors("Failed to import conversation")
async def import_conversation(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Override conversation title"),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Import a conversation from a JSON file.
    
    Supports importing conversations from JSON export files.
    Creates a new conversation with imported messages.
    
    Args:
        file: JSON file containing conversation data
        title: Override for conversation title
    """
    log_api_call("import_conversation", user_id=str(current_user.id))
    
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON files are supported for import"
            )
        
        # Read and parse file
        content = await file.read()
        try:
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        
        # Validate data structure
        if "messages" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation format: missing 'messages' field"
            )
        
        # Extract conversation info
        conversation_data = data.get("conversation", {})
        messages_data = data["messages"]
        
        if not messages_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages found in import file"
            )
        
        # Create new conversation
        conv_title = title or conversation_data.get("title", f"Imported conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        
        from ..schemas.conversation import ConversationCreate
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
                    name=msg_data.get("name")
                )
                
                conversation_service.db.add(message)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Failed to import message: {str(e)}")
        
        await conversation_service.db.commit()
        
        return {
            "success": True,
            "message": f"Conversation imported successfully with {imported_count} messages",
            "conversation_id": str(new_conversation.id),
            "conversation_title": conv_title,
            "imported_messages": imported_count,
            "total_messages": len(messages_data),
            "errors": errors[:5],  # Limit error reporting
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await conversation_service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/conversations/archive", response_model=BaseResponse)
@handle_api_errors("Failed to archive conversations")
async def archive_conversations(
    older_than_days: int = Query(90, ge=1, le=365, description="Archive conversations older than X days"),
    inactive_only: bool = Query(True, description="Archive only inactive conversations"),
    dry_run: bool = Query(True, description="Perform dry run without actually archiving"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive old conversations by marking them as inactive.
    
    Archives conversations based on age criteria to help manage
    database size and performance.
    
    Args:
        older_than_days: Archive conversations older than X days
        inactive_only: Archive only already inactive conversations
        dry_run: Perform dry run without actually archiving
        
    Requires superuser access.
    """
    log_api_call("archive_conversations", user_id=str(current_user.id), 
                older_than_days=older_than_days, inactive_only=inactive_only, dry_run=dry_run)
    
    try:
        # Build query
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        query = select(Conversation).where(Conversation.created_at < cutoff_date)
        
        if inactive_only:
            query = query.where(Conversation.is_active == False)
        else:
            query = query.where(Conversation.is_active == True)
        
        # Get conversations to archive
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        if dry_run:
            # Return preview
            preview = []
            for conv in conversations[:10]:  # Limit preview
                # Get message count
                msg_count = await db.scalar(
                    select(func.count(Message.id)).where(Message.conversation_id == conv.id)
                )
                
                preview.append({
                    "id": str(conv.id),
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "is_active": conv.is_active,
                    "message_count": msg_count or 0
                })
            
            return {
                "success": True,
                "message": f"Dry run: {len(conversations)} conversations would be archived",
                "total_count": len(conversations),
                "preview": preview,
                "criteria": {
                    "older_than_days": older_than_days,
                    "inactive_only": inactive_only,
                    "cutoff_date": cutoff_date.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Actually archive conversations
            archived_count = 0
            
            for conv in conversations:
                conv.is_active = False
                archived_count += 1
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Archived {archived_count} conversations successfully",
                "archived_count": archived_count,
                "criteria": {
                    "older_than_days": older_than_days,
                    "inactive_only": inactive_only,
                    "cutoff_date": cutoff_date.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Archive operation failed: {str(e)}"
        )


@router.get("/conversations/search", response_model=Dict[str, Any])
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
    """
    Search conversations and messages.
    
    Performs full-text search across conversation titles and message content
    with various filtering options.
    
    Args:
        query: Search query
        search_messages: Whether to search within message content
        user_filter: Username to filter by
        date_from: Start date for filtering
        date_to: End date for filtering
        active_only: Search only active conversations
        limit: Maximum number of results
    """
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
            filters.append(Conversation.is_active == True)
        
        # Date range filters
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                filters.append(Conversation.created_at >= date_from_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                filters.append(Conversation.created_at < date_to_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
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
            user_result = await db.execute(
                select(User).where(User.id == conv.user_id)
            )
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
                            Message.content.ilike(f"%{query}%")
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
                    
                    matching_messages.append({
                        "id": str(msg.id),
                        "role": msg.role,
                        "excerpt": excerpt,
                        "created_at": msg.created_at.isoformat()
                    })
            
            results.append({
                "id": str(conv.id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "is_active": conv.is_active,
                "message_count": msg_count or 0,
                "user": {
                    "username": user.username if user else "Unknown",
                    "email": user.email if user else "Unknown"
                },
                "matching_messages": matching_messages
            })
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_found": len(results),
                "search_criteria": {
                    "query": query,
                    "search_messages": search_messages,
                    "user_filter": user_filter,
                    "date_from": date_from,
                    "date_to": date_to,
                    "active_only": active_only,
                    "limit": limit
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/conversations/stats", response_model=Dict[str, Any])
@handle_api_errors("Failed to get conversation statistics")
async def get_conversation_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive conversation statistics.
    
    Returns detailed statistics about conversations including counts,
    activity metrics, and usage patterns.
    """
    log_api_call("get_conversation_statistics", user_id=str(current_user.id))
    
    try:
        # Basic conversation counts
        total_conversations = await db.scalar(select(func.count(Conversation.id)))
        active_conversations = await db.scalar(
            select(func.count(Conversation.id)).where(Conversation.is_active == True)
        )
        
        # Message statistics
        total_messages = await db.scalar(select(func.count(Message.id)))
        
        # Average messages per conversation
        avg_messages = await db.scalar(
            select(func.avg(func.count(Message.id)))
            .select_from(Message)
            .group_by(Message.conversation_id)
        ) or 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_conversations = await db.scalar(
            select(func.count(Conversation.id)).where(Conversation.created_at >= seven_days_ago)
        ) or 0
        
        recent_messages = await db.scalar(
            select(func.count(Message.id)).where(Message.created_at >= seven_days_ago)
        ) or 0
        
        # User engagement
        users_with_conversations = await db.scalar(
            select(func.count(func.distinct(Conversation.user_id)))
        ) or 0
        
        # Top active users by conversation count
        top_users = await db.execute(
            select(
                User.username,
                func.count(Conversation.id).label('conversation_count'),
                func.sum(
                    select(func.count(Message.id))
                    .where(Message.conversation_id == Conversation.id)
                    .scalar_subquery()
                ).label('total_messages')
            )
            .join(User, Conversation.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(func.count(Conversation.id).desc())
            .limit(5)
        )
        
        top_users_list = []
        for row in top_users.fetchall():
            top_users_list.append({
                "username": row.username,
                "conversation_count": row.conversation_count,
                "total_messages": row.total_messages or 0
            })
        
        # Message role distribution
        role_stats = await db.execute(
            select(
                Message.role,
                func.count(Message.id).label('count')
            )
            .group_by(Message.role)
        )
        
        role_distribution = {}
        for row in role_stats.fetchall():
            role_distribution[row.role] = row.count
        
        return {
            "success": True,
            "data": {
                "conversations": {
                    "total": total_conversations or 0,
                    "active": active_conversations or 0,
                    "inactive": (total_conversations or 0) - (active_conversations or 0)
                },
                "messages": {
                    "total": total_messages or 0,
                    "avg_per_conversation": round(avg_messages, 2),
                    "role_distribution": role_distribution
                },
                "recent_activity": {
                    "conversations_last_7_days": recent_conversations,
                    "messages_last_7_days": recent_messages
                },
                "user_engagement": {
                    "users_with_conversations": users_with_conversations,
                    "top_users": top_users_list
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation statistics: {str(e)}"
        )