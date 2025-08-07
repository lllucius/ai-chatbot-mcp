"""Document management API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional


from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import APIResponse
from shared.schemas.document import (
    BackgroundTaskResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    ProcessingConfigResponse,
    ProcessingStatusResponse,
    QueueStatusResponse,
)
from shared.schemas.document_responses import (
    AdvancedSearchData,
    BulkReprocessResponse,
    CleanupDeletedResponse,
    CleanupDryRunResponse,
    CleanupPreviewItem,
    DocumentFileTypeStats,
    DocumentProcessingStats,
    DocumentRecentActivity,
    DocumentSearchCriteria,
    DocumentSearchResult,
    DocumentStatisticsData,
    DocumentStorageStats,
    DocumentTopUser,
    DocumentUserInfo,
)

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user, get_document_service
from ..models.document import Document, FileStatus
from ..models.user import User
from ..services.background_processor import get_background_processor
from ..services.document import DocumentService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["documents"])


@router.post("/upload", response_model=APIResponse[DocumentUploadResponse])
@handle_api_errors("Failed to upload document")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    auto_process: bool = Form(default=True),
    processing_priority: int = Form(default=5, ge=1, le=10),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentUploadResponse]:
    """Upload a document for processing."""
    log_api_call(
        "upload_document", user_id=str(user.id), title=title, auto_process=auto_process
    )

    document = await service.create_document(file, title, user.id)

    task_id = None
    if auto_process:
        task_id = await service.start_processing(
            document.id, priority=processing_priority
        )

    document_response = DocumentResponse(
        id=document.id,
        title=document.title,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        mime_type=document.mime_type,
        processing_status=document.status,
        owner_id=document.owner_id,
        metainfo=document.metainfo,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )

    payload = DocumentUploadResponse(
        document=document_response,
        task_id=task_id,
        auto_processing=auto_process,
    )
    return APIResponse[DocumentUploadResponse](
        success=True,
        message="Document uploaded successfully",
        data=payload,
    )


@router.get("/", response_model=APIResponse[List[DocumentResponse]])
@handle_api_errors("Failed to retrieve documents")
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[List[DocumentResponse]]:
    """List user's documents with pagination and filtering."""
    log_api_call(
        "list_documents",
        user_id=str(current_user.id),
        page=page,
        size=size,
        file_type=file_type,
        status_filter=status_filter,
    )
    documents, total = await document_service.list_documents(
        user_id=current_user.id,
        page=page,
        size=size,
        file_type=file_type,
        status_filter=status_filter,
    )
    responses = [
        DocumentResponse(
            id=document.id,
            title=document.title,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            mime_type=document.mime_type,
            processing_status=document.status,
            owner_id=document.owner_id,
            metainfo=document.metainfo,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        for document in documents
    ]

    return APIResponse[List[DocumentResponse]](
        success=True,
        message="Documents retrieved successfully",
        data=responses,
    )


@router.get("/byid/{document_id}", response_model=APIResponse[DocumentResponse])
@handle_api_errors("Failed to retrieve document")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentResponse]:
    """Get document by ID."""
    log_api_call(
        "get_document", user_id=str(current_user.id), document_id=str(document_id)
    )
    document = await document_service.get_document(document_id, current_user.id)

    document_response = DocumentResponse(
        id=document.id,
        title=document.title,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        mime_type=document.mime_type,
        processing_status=document.status,
        owner_id=document.owner_id,
        metainfo=document.metainfo,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )

    return APIResponse[DocumentResponse](
        success=True, message="Document retrieved successfully", data=document_response
    )


@router.put("/byid/{document_id}", response_model=APIResponse[DocumentResponse])
@handle_api_errors("Document update failed")
async def update_document(
    document_id: str,
    request: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse[DocumentResponse]:
    """Update document metadata."""
    log_api_call(
        "update_document", user_id=str(current_user.id), document_id=str(document_id)
    )
    document = await document_service.update_document(
        document_id, request, current_user.id
    )
    payload = DocumentResponse.model_validate(document)
    return APIResponse[DocumentResponse](
        success=True,
        message="Document updated successfully",
        data=payload,
    )


@router.delete("/byid/{document_id}", response_model=APIResponse)
@handle_api_errors("Document deletion failed")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse:
    """Delete document and all associated data."""
    log_api_call(
        "delete_document", user_id=str(current_user.id), document_id=str(document_id)
    )
    success = await document_service.delete_document(document_id, current_user.id)

    if success:
        return APIResponse(
            success=True,
            message="Document deleted successfully",
        )
    else:
        return APIResponse(
            success=False,
            message="Document not found",
        )


@router.get(
    "/byid/{document_id}/status", response_model=APIResponse[ProcessingStatusResponse]
)
@handle_api_errors("Failed to get processing status", log_errors=True)
async def get_processing_status(
    document_id: str,
    task_id: Optional[str] = Query(
        None, description="Optional task ID for background processing details"
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> APIResponse[ProcessingStatusResponse]:
    """Get document processing status with optional background task information."""
    log_api_call(
        "get_processing_status",
        user_id=str(user.id),
        document_id=str(document_id),
        task_id=task_id,
    )
    if task_id:
        status_info = await service.get_processing_status(document_id, task_id)
        message = "Enhanced processing status retrieved"
    else:
        status_info = await service.get_processing_status(document_id, None)
        message = "Processing status retrieved"

    payload = ProcessingStatusResponse(
        success=True,
        message=message,
        document_id=document_id,
        status=status_info.get("status"),
        chunk_count=status_info.get("chunk_count", 0),
        processing_time=status_info.get("processing_time"),
        error_message=status_info.get("error_message"),
        created_at=status_info.get("created_at"),
        task_id=status_info.get("task_id"),
        task_status=status_info.get("task_status"),
        progress=status_info.get("progress"),
        task_created_at=status_info.get("task_created_at"),
        task_started_at=status_info.get("task_started_at"),
        task_error=status_info.get("task_error"),
    )

    return APIResponse[ProcessingStatusResponse](
        success=True,
        message=message,
        data=payload,
    )


@router.post("/byid/{document_id}/reprocess", response_model=APIResponse)
@handle_api_errors("Reprocessing failed for document", log_errors=True)
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> APIResponse:
    """Reprocess document."""
    log_api_call(
        "reprocess_document", user_id=str(current_user.id), document_id=str(document_id)
    )
    success = await document_service.reprocess_document(document_id, current_user.id)

    if success:
        return APIResponse(success=True, message="Document reprocessing started")
    else:
        return APIResponse(
            success=False, message="Cannot reprocess document at this time"
        )


@router.get("/byid/{document_id}/download")
@handle_api_errors("Download of document failed", log_errors=True)
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> FileResponse:
    """Download original document file."""
    log_api_call(
        "download_document", user_id=str(current_user.id), document_id=str(document_id)
    )
    file_path, filename, mime_type = await document_service.get_download_info(
        document_id, current_user.id
    )

    return FileResponse(path=file_path, filename=filename, media_type=mime_type)


@router.post(
    "/byid/{document_id}/process", response_model=APIResponse[BackgroundTaskResponse]
)
@handle_api_errors("Failed to start document processing", log_errors=True)
async def start_document_processing(
    document_id: str,
    priority: int = Query(
        default=5, ge=1, le=10, description="Processing priority (1=highest, 10=lowest)"
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> APIResponse[BackgroundTaskResponse]:
    """Start background processing for a document."""
    log_api_call(
        "start_document_processing",
        user_id=str(user.id),
        document_id=str(document_id),
        priority=priority,
    )
    task_id = await service.start_processing(document_id, priority=priority)

    payload = BackgroundTaskResponse(
        message="Document processing started",
        task_id=task_id,
        document_id=str(document_id),
        status="queued",
        priority=priority,
    )
    return APIResponse[BackgroundTaskResponse](
        success=True,
        message="Document processing started",
        data=payload,
    )


@router.get("/processing-config", response_model=APIResponse[ProcessingConfigResponse])
@handle_api_errors("Failed to retrieve configuration", log_errors=True)
async def get_processing_config() -> APIResponse[ProcessingConfigResponse]:
    """Get current document processing configuration."""
    log_api_call("get_processing_config")
    payload = ProcessingConfigResponse(
        message="Processing configuration retrieved",
        config={
            "default_chunk_size": settings.default_chunk_size,
            "default_chunk_overlap": settings.default_chunk_overlap,
            "max_chunk_size": settings.max_chunk_size,
            "min_chunk_size": settings.min_chunk_size,
            "max_chunk_overlap": settings.max_chunk_overlap,
            "enable_metadata_embedding": settings.enable_metadata_embedding,
            "embedding_batch_size": settings.embedding_batch_size,
            "enable_text_preprocessing": settings.enable_text_preprocessing,
            "normalize_unicode": settings.normalize_unicode,
            "remove_extra_whitespace": settings.remove_extra_whitespace,
            "language_detection": settings.language_detection,
            "max_concurrent_processing": settings.max_concurrent_processing,
            "processing_timeout": settings.processing_timeout,
            "supported_formats": settings.allowed_file_types,
        },
    )
    return APIResponse[ProcessingConfigResponse](
        success=True,
        message="Processing configuration retrieved",
        data=payload,
    )


@router.get("/queue-status", response_model=APIResponse[QueueStatusResponse])
@handle_api_errors("Failed to get queue status", log_errors=True)
async def get_queue_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[QueueStatusResponse]:
    """Get background processing queue status."""
    log_api_call("get_queue_status", user_id=str(user.id))
    background_processor = await get_background_processor()
    queue_status = await background_processor.get_queue_status()

    payload = QueueStatusResponse(
        success=True,
        message="Queue status retrieved",
        queue_size=queue_status.get("queue_size"),
        active_tasks=queue_status.get("active_tasks"),
        max_concurrent_tasks=queue_status.get("max_concurrent_tasks"),
        completed_tasks=queue_status.get("completed_tasks"),
        worker_running=queue_status.get("worker_running"),
    )

    return APIResponse[QueueStatusResponse](
        success=True,
        message="Queue status retrieved",
        data=payload,
    )


@router.post("cleanup", response_model=APIResponse)
@handle_api_errors("Failed to cleanup documents")
async def cleanup_documents(
    status_filter: Optional[str] = Query(
        None, description="Status to filter by: failed, completed, processing"
    ),
    older_than_days: int = Query(
        30, ge=1, le=365, description="Remove documents older than X days"
    ),
    dry_run: bool = Query(
        True, description="Perform dry run without actually deleting"
    ),
    current_user: User = Depends(get_current_superuser),
    document_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """Clean up old or failed documents."""
    log_api_call(
        "cleanup_documents",
        user_id=str(current_user.id),
        status_filter=status_filter,
        older_than_days=older_than_days,
        dry_run=dry_run,
    )

    # Build query
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
    query = select(Document).where(Document.created_at < cutoff_date)

    # Apply status filter
    if status_filter:
        status_map = {
            "failed": FileStatus.FAILED,
            "completed": FileStatus.COMPLETED,
            "processing": FileStatus.PROCESSING,
            "pending": FileStatus.PENDING,
        }

        if status_filter not in status_map:
            return APIResponse(
                success=False,
                message=f"Invalid status filter. Use one of: {list(status_map.keys())}",
            )

        query = query.where(Document.status == status_map[status_filter])

    # Get documents to be deleted
    result = await db.execute(query)
    documents = result.scalars().all()

    if dry_run:
        preview = []
        for doc in documents[:10]:  # Limit preview to 10 items
            preview.append(
                CleanupPreviewItem(
                    id=str(doc.id),
                    title=doc.title,
                    status=doc.status.value,
                    created_at=doc.created_at.isoformat(),
                    file_size=doc.file_size,
                )
            )

        criteria = {
            "status_filter": status_filter,
            "older_than_days": older_than_days,
            "cutoff_date": cutoff_date.isoformat(),
        }

        payload = CleanupDryRunResponse(
            total_count=len(documents),
            preview=preview,
            total_size_bytes=sum(doc.file_size or 0 for doc in documents),
            criteria=criteria,
        )

        return APIResponse[CleanupDryRunResponse](
            success=True,
            message=f"Dry run: {len(documents)} documents would be deleted",
            data=payload,
        )
    else:
        deleted_count = 0
        deleted_size = 0
        errors = []

        for doc in documents:
            try:
                await document_service.delete_document(doc.id)
                deleted_count += 1
                deleted_size += doc.file_size or 0
            except Exception as e:
                errors.append(f"Failed to delete document {doc.id}: {str(e)}")

        criteria = {
            "status_filter": status_filter,
            "older_than_days": older_than_days,
            "cutoff_date": cutoff_date.isoformat(),
        }

        payload = CleanupDeletedResponse(
            deleted_count=deleted_count,
            deleted_size_bytes=deleted_size,
            errors=errors[:5],  # Limit error reporting
            criteria=criteria,
        )

        return APIResponse[CleanupDeletedResponse](
            success=True,
            message=f"Cleanup completed: {deleted_count} documents deleted",
            data=payload,
        )


@router.get("/stats", response_model=APIResponse[DocumentStatisticsData])
@handle_api_errors("Failed to get document statistics")
async def get_document_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentStatisticsData]:
    """Get comprehensive document statistics."""
    log_api_call("get_document_statistics", user_id=str(current_user.id))

    # Basic counts by status
    status_counts = {}
    for stat in FileStatus:
        count = await db.scalar(
            select(func.count(Document.id)).where(Document.status == stat)
        )
        status_counts[stat.value] = count or 0

    # Total storage usage
    total_size = (
        await db.scalar(
            select(func.sum(Document.file_size)).where(Document.file_size.is_not(None))
        )
        or 0
    )

    # File type distribution
    file_types = await db.execute(
        select(
            func.lower(func.split_part(Document.file_name, ".", -1)).label("extension"),
            func.count(Document.id).label("count"),
            func.sum(Document.file_size).label("total_size"),
        )
        .group_by(func.lower(func.split_part(Document.file_name, ".", -1)))
        .order_by(func.count(Document.id).desc())
        .limit(10)
    )

    file_type_stats = []
    for row in file_types.fetchall():
        file_type_stats.append(
            DocumentFileTypeStats(
                extension=row.extension or "unknown",
                count=row.count,
                total_size=row.total_size or 0,
            )
        )

    # Processing performance
    avg_processing_time = (
        await db.scalar(
            select(
                func.avg(
                    func.extract("epoch", Document.updated_at - Document.created_at)
                )
            ).where(
                and_(
                    Document.status == FileStatus.COMPLETED,
                    Document.updated_at.is_not(None),
                )
            )
        )
        or 0
    )

    # Recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = (
        await db.scalar(
            select(func.count(Document.id)).where(Document.created_at >= seven_days_ago)
        )
        or 0
    )

    recent_processed = (
        await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.updated_at >= seven_days_ago,
                    Document.status == FileStatus.COMPLETED,
                )
            )
        )
        or 0
    )

    # Top uploaders
    top_uploaders = await db.execute(
        select(
            User.username,
            func.count(Document.id).label("document_count"),
            func.sum(Document.file_size).label("total_size"),
        )
        .join(User, Document.user_id == User.id)
        .group_by(User.id, User.username)
        .order_by(func.count(Document.id).desc())
        .limit(5)
    )

    top_users = []
    for row in top_uploaders.fetchall():
        top_users.append(
            DocumentTopUser(
                username=row.username,
                document_count=row.document_count,
                total_size_bytes=row.total_size or 0,
            )
        )

    # Calculate success rate
    total_processed = status_counts.get("completed", 0) + status_counts.get("failed", 0)
    success_rate = (status_counts.get("completed", 0) / max(total_processed, 1)) * 100

    # Create structured data models
    storage_stats = DocumentStorageStats(
        total_size_bytes=total_size,
        total_size_mb=round(total_size / 1024 / 1024, 2),
        avg_file_size_bytes=round(total_size / max(sum(status_counts.values()), 1), 2),
    )

    processing_stats = DocumentProcessingStats(
        success_rate=round(success_rate, 2),
        avg_processing_time_seconds=round(avg_processing_time, 2),
        total_processed=total_processed,
    )

    recent_activity = DocumentRecentActivity(
        uploads_last_7_days=recent_uploads,
        processed_last_7_days=recent_processed,
    )

    response_payload = DocumentStatisticsData(
        counts_by_status=status_counts,
        total_documents=sum(status_counts.values()),
        storage=storage_stats,
        file_types=file_type_stats,
        processing=processing_stats,
        recent_activity=recent_activity,
        top_uploaders=top_users,
        timestamp=datetime.utcnow().isoformat(),
    )

    return APIResponse[DocumentStatisticsData](
        success=True,
        message="Document statistics retrieved successfully",
        data=response_payload,
    )


@router.post(
    "/bulk-reprocess", response_model=APIResponse[BulkReprocessResponse]
)
@handle_api_errors("Failed to bulk reprocess documents")
async def bulk_reprocess_documents(
    status_filter: str = Query(
        "failed", description="Status to filter by: failed, completed"
    ),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of documents to reprocess"
    ),
    current_user: User = Depends(get_current_superuser),
    document_service: DocumentService = Depends(get_document_service),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BulkReprocessResponse]:
    """Bulk reprocess documents based on status filter."""
    log_api_call(
        "bulk_reprocess_documents",
        user_id=str(current_user.id),
        status_filter=status_filter,
        limit=limit,
    )

    status_map = {"failed": FileStatus.FAILED, "completed": FileStatus.COMPLETED}

    if status_filter not in status_map:
        payload = BulkReprocessResponse(
            reprocessed_count=0,
            total_found=0,
            errors=[f"Invalid status filter. Use one of: {list(status_map.keys())}"],
            criteria={"status_filter": status_filter, "limit": limit},
        )
        return APIResponse[BulkReprocessResponse](
            success=False,
            message=f"Invalid status filter. Use one of: {list(status_map.keys())}",
            data=payload,
        )

    query = (
        select(Document)
        .where(Document.status == status_map[status_filter])
        .limit(limit)
    )

    result = await db.execute(query)
    documents = result.scalars().all()

    if not documents:
        payload = BulkReprocessResponse(
            reprocessed_count=0,
            total_found=0,
            errors=[],
            criteria={"status_filter": status_filter, "limit": limit},
        )
        return APIResponse[BulkReprocessResponse](
            success=True,
            message=f"No documents found with status '{status_filter}' to reprocess",
            data=payload,
        )

    reprocessed_count = 0
    errors = []

    for doc in documents:
        try:
            await document_service.reprocess_document(doc.id)
            reprocessed_count += 1
        except Exception as e:
            errors.append(
                f"Failed to reprocess document {doc.id} ({doc.title}): {str(e)}"
            )

    payload = BulkReprocessResponse(
        reprocessed_count=reprocessed_count,
        total_found=len(documents),
        errors=errors[:5],
        criteria={"status_filter": status_filter, "limit": limit},
    )

    return APIResponse[BulkReprocessResponse](
        success=True,
        message=f"Bulk reprocessing initiated for {reprocessed_count} documents",
        data=payload,
    )


@router.get(
    "/search/advanced", response_model=APIResponse[AdvancedSearchData]
)
@handle_api_errors("Failed to perform advanced document search")
async def advanced_document_search(
    query: str = Query(..., description="Search query"),
    file_types: Optional[str] = Query(
        None, description="Comma-separated file extensions (e.g., pdf,docx)"
    ),
    status_filter: Optional[str] = Query(
        None, description="Status filter: completed, failed, processing"
    ),
    user_filter: Optional[str] = Query(None, description="Username to filter by"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_size: Optional[int] = Query(
        None, ge=0, description="Minimum file size in bytes"
    ),
    max_size: Optional[int] = Query(
        None, ge=0, description="Maximum file size in bytes"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AdvancedSearchData]:
    """Perform advanced document search with multiple filters."""
    log_api_call("advanced_document_search", user_id=str(current_user.id), query=query)

    base_query = select(Document).join(User, Document.user_id == User.id)

    filters = []

    # Text search in title and content
    if query:
        text_filter = or_(
            Document.title.ilike(f"%{query}%"),
            (
                Document.content.ilike(f"%{query}%")
                if hasattr(Document, "content")
                else False
            ),
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
            "pending": FileStatus.PENDING,
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
            return APIResponse(
                success=False,
                message="Invalid date_from format. Use YYYY-MM-DD",
            )

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            filters.append(Document.created_at < date_to_obj)
        except ValueError:
            return APIResponse(
                success=False,
                message="Invalid date_to format. Use YYYY-MM-DD",
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
        user_result = await db.execute(select(User).where(User.id == doc.user_id))
        user = user_result.scalar_one_or_none()
        user_info = DocumentUserInfo(
            username=user.username if user else "Unknown",
            email=user.email if user else "Unknown",
        )
        results.append(
            DocumentSearchResult(
                id=str(doc.id),
                title=doc.title,
                file_name=doc.file_name,
                file_size=doc.file_size,
                status=doc.status.value,
                created_at=doc.created_at.isoformat(),
                updated_at=(doc.updated_at.isoformat() if doc.updated_at else None),
                user=user_info,
                error_message=doc.error_message,
            )
        )

    search_criteria = DocumentSearchCriteria(
        query=query,
        file_types=file_types,
        status_filter=status_filter,
        user_filter=user_filter,
        date_from=date_from,
        date_to=date_to,
        min_size=min_size,
        max_size=max_size,
        limit=limit,
    )

    response_payload = AdvancedSearchData(
        results=results,
        total_found=len(results),
        search_criteria=search_criteria,
        timestamp=datetime.utcnow().isoformat(),
    )

    return APIResponse[AdvancedSearchData](
        success=True,
        message="Advanced document search completed successfully",
        data=response_payload,
    )
