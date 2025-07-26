"""
Extended document management API endpoints.

This module provides additional document management endpoints that extend
the base document API with administrative and advanced operations.

Key Features:
- Document cleanup operations
- Bulk document operations
- Advanced search and filtering
- Document statistics and analytics
- Administrative document management

"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.document import Document, FileStatus
from ..models.user import User
from ..schemas.common import BaseResponse
from ..services.document import DocumentService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["document-admin"])


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)


@router.post("/documents/cleanup", response_model=BaseResponse)
@handle_api_errors("Failed to cleanup documents")
async def cleanup_documents(
    status_filter: Optional[str] = Query(None, description="Status to filter by: failed, completed, processing"),
    older_than_days: int = Query(30, ge=1, le=365, description="Remove documents older than X days"),
    dry_run: bool = Query(True, description="Perform dry run without actually deleting"),
    current_user: User = Depends(get_current_superuser),
    document_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Clean up old or failed documents.
    
    Removes documents based on age and status criteria.
    Supports dry run mode to preview what would be deleted.
    
    Args:
        status_filter: Status to filter by (failed, completed, processing)
        older_than_days: Remove documents older than X days
        dry_run: Perform dry run without actually deleting
        
    Requires superuser access.
    """
    log_api_call("cleanup_documents", user_id=str(current_user.id), 
                status_filter=status_filter, older_than_days=older_than_days, dry_run=dry_run)
    
    try:
        # Build query
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        query = select(Document).where(Document.created_at < cutoff_date)
        
        # Apply status filter
        if status_filter:
            status_map = {
                "failed": FileStatus.FAILED,
                "completed": FileStatus.COMPLETED,
                "processing": FileStatus.PROCESSING,
                "pending": FileStatus.PENDING
            }
            
            if status_filter not in status_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Use one of: {list(status_map.keys())}"
                )
            
            query = query.where(Document.status == status_map[status_filter])
        
        # Get documents to be deleted
        result = await db.execute(query)
        documents = result.scalars().all()
        
        if dry_run:
            # Return preview of what would be deleted
            preview = []
            for doc in documents[:10]:  # Limit preview to 10 items
                preview.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "status": doc.status.value,
                    "created_at": doc.created_at.isoformat(),
                    "file_size": doc.file_size
                })
            
            return {
                "success": True,
                "message": f"Dry run: {len(documents)} documents would be deleted",
                "total_count": len(documents),
                "preview": preview,
                "total_size_bytes": sum(doc.file_size or 0 for doc in documents),
                "criteria": {
                    "status_filter": status_filter,
                    "older_than_days": older_than_days,
                    "cutoff_date": cutoff_date.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Actually delete documents
            deleted_count = 0
            deleted_size = 0
            errors = []
            
            for doc in documents:
                try:
                    # Delete associated chunks and embeddings
                    await document_service.delete_document(doc.id)
                    deleted_count += 1
                    deleted_size += doc.file_size or 0
                except Exception as e:
                    errors.append(f"Failed to delete document {doc.id}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Cleanup completed: {deleted_count} documents deleted",
                "deleted_count": deleted_count,
                "deleted_size_bytes": deleted_size,
                "errors": errors[:5],  # Limit error reporting
                "criteria": {
                    "status_filter": status_filter,
                    "older_than_days": older_than_days,
                    "cutoff_date": cutoff_date.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document cleanup failed: {str(e)}"
        )


@router.get("/documents/stats", response_model=Dict[str, Any])
@handle_api_errors("Failed to get document statistics")
async def get_document_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive document statistics.
    
    Returns detailed statistics about documents including counts by status,
    file types, processing metrics, and storage usage.
    """
    log_api_call("get_document_statistics", user_id=str(current_user.id))
    
    try:
        # Basic counts by status
        status_counts = {}
        for stat in FileStatus:
            count = await db.scalar(
                select(func.count(Document.id)).where(Document.status == stat)
            )
            status_counts[stat.value] = count or 0
        
        # Total storage usage
        total_size = await db.scalar(
            select(func.sum(Document.file_size)).where(Document.file_size.is_not(None))
        ) or 0
        
        # File type distribution
        file_types = await db.execute(
            select(
                func.lower(func.split_part(Document.file_name, '.', -1)).label('extension'),
                func.count(Document.id).label('count'),
                func.sum(Document.file_size).label('total_size')
            )
            .group_by(func.lower(func.split_part(Document.file_name, '.', -1)))
            .order_by(func.count(Document.id).desc())
            .limit(10)
        )
        
        file_type_stats = []
        for row in file_types.fetchall():
            file_type_stats.append({
                "extension": row.extension,
                "count": row.count,
                "total_size_bytes": row.total_size or 0
            })
        
        # Processing performance
        avg_processing_time = await db.scalar(
            select(func.avg(
                func.extract('epoch', Document.updated_at - Document.created_at)
            )).where(
                and_(
                    Document.status == FileStatus.COMPLETED,
                    Document.updated_at.is_not(None)
                )
            )
        ) or 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = await db.scalar(
            select(func.count(Document.id)).where(Document.created_at >= seven_days_ago)
        ) or 0
        
        recent_processed = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.updated_at >= seven_days_ago,
                    Document.status == FileStatus.COMPLETED
                )
            )
        ) or 0
        
        # Top uploaders
        top_uploaders = await db.execute(
            select(
                User.username,
                func.count(Document.id).label('document_count'),
                func.sum(Document.file_size).label('total_size')
            )
            .join(User, Document.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(func.count(Document.id).desc())
            .limit(5)
        )
        
        top_users = []
        for row in top_uploaders.fetchall():
            top_users.append({
                "username": row.username,
                "document_count": row.document_count,
                "total_size_bytes": row.total_size or 0
            })
        
        # Calculate success rate
        total_processed = status_counts.get("completed", 0) + status_counts.get("failed", 0)
        success_rate = (status_counts.get("completed", 0) / max(total_processed, 1)) * 100
        
        return {
            "success": True,
            "data": {
                "counts_by_status": status_counts,
                "total_documents": sum(status_counts.values()),
                "storage": {
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / 1024 / 1024, 2),
                    "avg_file_size_bytes": round(total_size / max(sum(status_counts.values()), 1), 2)
                },
                "file_types": file_type_stats,
                "processing": {
                    "success_rate": round(success_rate, 2),
                    "avg_processing_time_seconds": round(avg_processing_time, 2),
                    "total_processed": total_processed
                },
                "recent_activity": {
                    "uploads_last_7_days": recent_uploads,
                    "processed_last_7_days": recent_processed
                },
                "top_uploaders": top_users,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document statistics: {str(e)}"
        )


@router.post("/documents/bulk-reprocess", response_model=BaseResponse)
@handle_api_errors("Failed to bulk reprocess documents")
async def bulk_reprocess_documents(
    status_filter: str = Query("failed", description="Status to filter by: failed, completed"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents to reprocess"),
    current_user: User = Depends(get_current_superuser),
    document_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk reprocess documents based on status filter.
    
    Initiates reprocessing for multiple documents matching the criteria.
    Useful for recovering from processing failures or applying updates.
    
    Args:
        status_filter: Status to filter by (failed, completed)
        limit: Maximum number of documents to reprocess
        
    Requires superuser access.
    """
    log_api_call("bulk_reprocess_documents", user_id=str(current_user.id), 
                status_filter=status_filter, limit=limit)
    
    try:
        # Validate status filter
        status_map = {
            "failed": FileStatus.FAILED,
            "completed": FileStatus.COMPLETED
        }
        
        if status_filter not in status_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Use one of: {list(status_map.keys())}"
            )
        
        # Get documents to reprocess
        query = (
            select(Document)
            .where(Document.status == status_map[status_filter])
            .limit(limit)
        )
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        if not documents:
            return {
                "success": True,
                "message": f"No documents found with status '{status_filter}' to reprocess",
                "reprocessed_count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Reprocess documents
        reprocessed_count = 0
        errors = []
        
        for doc in documents:
            try:
                await document_service.reprocess_document(doc.id)
                reprocessed_count += 1
            except Exception as e:
                errors.append(f"Failed to reprocess document {doc.id} ({doc.title}): {str(e)}")
        
        return {
            "success": True,
            "message": f"Bulk reprocessing initiated for {reprocessed_count} documents",
            "reprocessed_count": reprocessed_count,
            "total_found": len(documents),
            "errors": errors[:5],  # Limit error reporting
            "criteria": {
                "status_filter": status_filter,
                "limit": limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk reprocessing failed: {str(e)}"
        )


@router.get("/documents/search/advanced", response_model=Dict[str, Any])
@handle_api_errors("Failed to perform advanced document search")
async def advanced_document_search(
    query: str = Query(..., description="Search query"),
    file_types: Optional[str] = Query(None, description="Comma-separated file extensions (e.g., pdf,docx)"),
    status_filter: Optional[str] = Query(None, description="Status filter: completed, failed, processing"),
    user_filter: Optional[str] = Query(None, description="Username to filter by"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_size: Optional[int] = Query(None, ge=0, description="Minimum file size in bytes"),
    max_size: Optional[int] = Query(None, ge=0, description="Maximum file size in bytes"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform advanced document search with multiple filters.
    
    Supports complex filtering by content, metadata, file properties,
    user ownership, and date ranges.
    
    Args:
        query: Search query for content and title
        file_types: Comma-separated file extensions to filter by
        status_filter: Status filter
        user_filter: Username to filter by
        date_from: Start date for filtering
        date_to: End date for filtering
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        limit: Maximum number of results
    """
    log_api_call("advanced_document_search", user_id=str(current_user.id), query=query)
    
    try:
        # Build base query
        base_query = select(Document).join(User, Document.user_id == User.id)
        
        # Apply filters
        filters = []
        
        # Text search in title and content
        if query:
            text_filter = or_(
                Document.title.ilike(f"%{query}%"),
                Document.content.ilike(f"%{query}%") if hasattr(Document, 'content') else False
            )
            filters.append(text_filter)
        
        # File type filter
        if file_types:
            extensions = [ext.strip().lower() for ext in file_types.split(",")]
            file_type_filters = []
            for ext in extensions:
                file_type_filters.append(Document.file_name.ilike(f"%.{ext}"))
            filters.append(or_(*file_type_filters))
        
        # Status filter
        if status_filter:
            status_map = {
                "completed": FileStatus.COMPLETED,
                "failed": FileStatus.FAILED,
                "processing": FileStatus.PROCESSING,
                "pending": FileStatus.PENDING
            }
            if status_filter in status_map:
                filters.append(Document.status == status_map[status_filter])
        
        # User filter
        if user_filter:
            filters.append(User.username.ilike(f"%{user_filter}%"))
        
        # Date range filters
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                filters.append(Document.created_at >= date_from_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                filters.append(Document.created_at < date_to_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )
        
        # File size filters
        if min_size is not None:
            filters.append(Document.file_size >= min_size)
        
        if max_size is not None:
            filters.append(Document.file_size <= max_size)
        
        # Apply all filters
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Add ordering and limit
        base_query = base_query.order_by(Document.created_at.desc()).limit(limit)
        
        # Execute query
        result = await db.execute(base_query)
        documents = result.scalars().all()
        
        # Format results
        results = []
        for doc in documents:
            # Get user info
            user_result = await db.execute(
                select(User).where(User.id == doc.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "file_name": doc.file_name,
                "file_size": doc.file_size,
                "status": doc.status.value,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "user": {
                    "username": user.username if user else "Unknown",
                    "email": user.email if user else "Unknown"
                },
                "error_message": doc.error_message
            })
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_found": len(results),
                "search_criteria": {
                    "query": query,
                    "file_types": file_types,
                    "status_filter": status_filter,
                    "user_filter": user_filter,
                    "date_from": date_from,
                    "date_to": date_to,
                    "min_size": min_size,
                    "max_size": max_size,
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
            detail=f"Advanced search failed: {str(e)}"
        )
