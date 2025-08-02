"""
Document management API endpoints with comprehensive processing capabilities.

This module provides endpoints for document upload, processing, management,
and retrieval operations with full lifecycle support including background
processing, status monitoring, and advanced search capabilities.

Key Features:
- Document upload with multiple format support
- Background processing with priority queuing
- Real-time status monitoring and progress tracking
- Document reprocessing and error recovery
- Bulk operations for administrative management
- Advanced search and filtering capabilities
- Export functionality in multiple formats

Processing Pipeline:
- Text extraction from various file formats
- Intelligent chunking with configurable parameters
- Embedding generation for semantic search
- Metadata extraction and indexing
- Quality validation and error handling

Security Features:
- User-based document ownership and access control
- File type validation and sanitization
- Processing quota management
- Comprehensive audit logging
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user, get_document_service
from ..models.document import Document, FileStatus
from ..models.user import User
from ..schemas.admin import AdvancedSearchResponse, DocumentStatsResponse
from ..schemas.common import BaseResponse, PaginatedResponse
from ..schemas.document import (
    BackgroundTaskResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    ProcessingConfigResponse,
    ProcessingStatusResponse,
    QueueStatusResponse,
)
from ..services.background_processor import get_background_processor
from ..services.document import DocumentService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
@handle_api_errors("Failed to upload document")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    auto_process: bool = Form(default=True),
    processing_priority: int = Form(default=5, ge=1, le=10),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """
    Upload a document for processing with configurable options.

    Uploads a document file to the platform and optionally starts automatic
    processing including text extraction, chunking, and embedding generation.
    Supports various file formats and priority-based processing.

    Args:
        file: Document file to upload (various formats supported)
        title: Human-readable title for the document
        auto_process: Whether to automatically start processing after upload
        processing_priority: Processing priority level (1-10, higher = more priority)
        user: Current authenticated user from JWT token
        service: Injected document service instance

    Returns:
        DocumentUploadResponse: Upload result containing:
            - document: Created document metadata
            - task_id: Background processing task ID (if auto_process=true)
            - processing_status: Initial processing status
            - upload_info: File upload information and statistics

    Supported File Types:
        - PDF documents (.pdf)
        - Microsoft Word (.docx, .doc)
        - Plain text files (.txt)
        - Markdown files (.md)
        - HTML files (.html)

    Processing Pipeline:
        - Text extraction from uploaded file
        - Intelligent content chunking
        - Embedding generation for semantic search
        - Metadata extraction and indexing

    Raises:
        HTTP 400: If file type is not supported or file is corrupted
        HTTP 413: If file size exceeds configured limits
        HTTP 500: If upload or processing initialization fails

    Example:
        POST /api/v1/documents/upload
        Content-Type: multipart/form-data

        file: [document.pdf]
        title: "Project Requirements"
        auto_process: true
        processing_priority: 7
    """
    log_api_call(
        "upload_document", user_id=str(user.id), title=title, auto_process=auto_process
    )

    # Create document
    document = await service.create_document(file, title, user.id)

    task_id = None
    if auto_process:
        # Start background processing
        task_id = await service.start_processing(
            document.id, priority=processing_priority
        )

    return DocumentUploadResponse(
        success=True,
        message="Document uploaded successfully",
        document=DocumentResponse.model_validate(document),
        task_id=task_id,
        auto_processing=auto_process,
    )


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
@handle_api_errors("Failed to retrieve documents")
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    List user's documents with pagination and filtering.

    Returns paginated list of documents owned by the current user
    with optional filtering by file type and processing status.

    Args:
        page: Page number for pagination (starting from 1)
        size: Number of documents per page (1-100)
        file_type: Optional filter by file type (e.g., 'pdf', 'docx')
        status_filter: Optional filter by processing status
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        PaginatedResponse[DocumentResponse]: Paginated list of user documents
    """
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
    responses = []
    for document in documents:
        response = {
            "id": document.id,
            "title": document.title,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "processing_status": document.status,
            "owner_id": document.owner_id,
            "metainfo": document.metainfo,
            "chunk_count": document.chunk_count,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
        responses.append(DocumentResponse.model_validate(response))

    return PaginatedResponse.create(
        items=responses,
        total=total,
        page=page,
        size=size,
        message="Documents retrieved successfully",
    )


@router.get("/byid/{document_id}", response_model=DocumentResponse)
@handle_api_errors("Failed to retrieve document")
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get document by ID.

    Returns detailed information about a specific document
    owned by the current user, including processing status,
    metadata, and chunk information.

    Args:
        document_id: UUID of the document to retrieve
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        DocumentResponse: Complete document information

    Raises:
        HTTP 404: If document not found or not owned by user
    """
    log_api_call("get_document", user_id=str(current_user.id), document_id=str(document_id))
    document = await document_service.get_document(document_id, current_user.id)
    response = {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "processing_status": document.status,
        "owner_id": document.owner_id,
        "metainfo": document.metainfo,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }
    return DocumentResponse.model_validate(response)


@router.put("/byid/{document_id}", response_model=DocumentResponse)
@handle_api_errors("Document update failed")
async def update_document(
    document_id: UUID,
    request: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Update document metadata.

    Allows updating document title and metadata.
    Cannot change the actual file content.

    Args:
        document_id: UUID of the document to update
        request: Document update data (title, metadata)
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        DocumentResponse: Updated document information

    Raises:
        HTTP 404: If document not found or not owned by user
    """
    log_api_call("update_document", user_id=str(current_user.id), document_id=str(document_id))
    document = await document_service.update_document(
        document_id, request, current_user.id
    )
    return DocumentResponse.model_validate(document)


@router.delete("/byid/{document_id}", response_model=BaseResponse)
@handle_api_errors("Document deletion failed")
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Delete document and all associated data.

    Permanently deletes the document, its chunks, embeddings,
    and removes the file from storage.

    Args:
        document_id: UUID of the document to delete
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        BaseResponse: Confirmation of successful deletion

    Raises:
        HTTP 404: If document not found or not owned by user
    """
    log_api_call("delete_document", user_id=str(current_user.id), document_id=str(document_id))
    success = await document_service.delete_document(document_id, current_user.id)

    if success:
        return BaseResponse(success=True, message="document deleted successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="document not found"
        )


@router.get("/byid/{document_id}/status", response_model=ProcessingStatusResponse)
@handle_api_errors("Failed to get processing status", log_errors=True)
async def get_processing_status(
    document_id: UUID,
    task_id: Optional[str] = Query(
        None, description="Optional task ID for background processing details"
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> ProcessingStatusResponse:
    """
    Get document processing status with optional background task information.

    Returns current processing status, progress, and any error information
    for the specified document. Can include background task details if task_id is provided.

    Args:
        document_id: UUID of the document to check
        task_id: Optional background task ID for detailed status
        user: Current authenticated user
        service: Document service instance

    Returns:
        ProcessingStatusResponse: Document processing status and progress
    """
    log_api_call("get_processing_status", user_id=str(user.id), document_id=str(document_id), task_id=task_id)
    if task_id:
        # Enhanced processing status with task details
        status_info = await service.get_processing_status(document_id, task_id)
        message = "Enhanced processing status retrieved"
    else:
        # Basic processing status
        status_info = await service.get_processing_status(document_id, None)
        message = "Processing status retrieved"

    return ProcessingStatusResponse(success=True, message=message, **status_info)


@router.post("/byid/{document_id}/reprocess", response_model=BaseResponse)
@handle_api_errors("Reprocessing failed for document", log_errors=True)
async def reprocess_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Reprocess document.

    Triggers reprocessing of the document, including text extraction,
    chunking, and embedding generation. Useful if processing failed
    or if you want to update with new processing parameters.

    Args:
        document_id: UUID of the document to reprocess
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        BaseResponse: Confirmation that reprocessing has started

    Raises:
        HTTP 400: If document cannot be reprocessed at this time
        HTTP 404: If document not found or not owned by user
    """
    log_api_call("reprocess_document", user_id=str(current_user.id), document_id=str(document_id))
    success = await document_service.reprocess_document(document_id, current_user.id)

    if success:
        return BaseResponse(success=True, message="Document reprocessing started")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reprocess document at this time",
        )


@router.get("/byid/{document_id}/download")
@handle_api_errors("Download of document failed", log_errors=True)
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> FileResponse:
    """
    Download original document file.

    Returns the original uploaded file for download.

    Args:
        document_id: UUID of the document to download
        current_user: Current authenticated user
        document_service: Document service instance

    Returns:
        FileResponse: Original document file for download

    Raises:
        HTTP 404: If document not found or not owned by user
    """
    log_api_call("download_document", user_id=str(current_user.id), document_id=str(document_id))
    file_path, filename, mime_type = await document_service.get_download_info(
        document_id, current_user.id
    )

    from fastapi.responses import FileResponse

    return FileResponse(path=file_path, filename=filename, media_type=mime_type)


@router.post("/byid/{document_id}/process", response_model=BackgroundTaskResponse)
@handle_api_errors("Failed to start document processing", log_errors=True)
async def start_document_processing(
    document_id: UUID,
    priority: int = Query(
        default=5, ge=1, le=10, description="Processing priority (1=highest, 10=lowest)"
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> BackgroundTaskResponse:
    """
    Start background processing for a document.

    Initiates text extraction, chunking, and embedding generation.

    Args:
        document_id: UUID of the document to process
        priority: Processing priority from 1 (highest) to 10 (lowest)
        user: Current authenticated user
        service: Document service instance

    Returns:
        BackgroundTaskResponse: Task information including task ID and status
    """
    log_api_call("start_document_processing", user_id=str(user.id), document_id=str(document_id), priority=priority)
    task_id = await service.start_processing(document_id, priority=priority)

    return BackgroundTaskResponse(
        message="Document processing started",
        task_id=task_id,
        document_id=str(document_id),
        status="queued",
    )


@router.get("/processing-config", response_model=ProcessingConfigResponse)
@handle_api_errors("Failed to retrieve configuration", log_errors=True)
async def get_processing_config() -> ProcessingConfigResponse:
    """
    Get current document processing configuration.

    Returns the current settings for chunk sizes, overlaps, and other processing parameters.

    Returns:
        ProcessingConfigResponse: Current processing configuration settings
    """
    log_api_call("get_processing_config")
    return ProcessingConfigResponse(
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


@router.get("/queue-status", response_model=QueueStatusResponse)
@handle_api_errors("Failed to get queue status", log_errors=True)
async def get_queue_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get background processing queue status.

    Provides information about current queue size, active tasks, and processing capacity.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        QueueStatusResponse: Current queue status and processing information
    """
    log_api_call("get_queue_status", user_id=str(user.id))
    background_processor = await get_background_processor(db)
    queue_status = await background_processor.get_queue_status()

    return QueueStatusResponse(
        success=True, message="Queue status retrieved", **queue_status
    )


@router.post("/documents/cleanup", response_model=BaseResponse)
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
    log_api_call(
        "cleanup_documents",
        user_id=str(current_user.id),
        status_filter=status_filter,
        older_than_days=older_than_days,
        dry_run=dry_run,
    )

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
                "pending": FileStatus.PENDING,
            }

            if status_filter not in status_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Use one of: {list(status_map.keys())}",
                )

            query = query.where(Document.status == status_map[status_filter])

        # Get documents to be deleted
        result = await db.execute(query)
        documents = result.scalars().all()

        if dry_run:
            # Return preview of what would be deleted
            preview = []
            for doc in documents[:10]:  # Limit preview to 10 items
                preview.append(
                    {
                        "id": str(doc.id),
                        "title": doc.title,
                        "status": doc.status.value,
                        "created_at": doc.created_at.isoformat(),
                        "file_size": doc.file_size,
                    }
                )

            return {
                "success": True,
                "message": f"Dry run: {len(documents)} documents would be deleted",
                "total_count": len(documents),
                "preview": preview,
                "total_size_bytes": sum(doc.file_size or 0 for doc in documents),
                "criteria": {
                    "status_filter": status_filter,
                    "older_than_days": older_than_days,
                    "cutoff_date": cutoff_date.isoformat(),
                },
                "timestamp": datetime.utcnow().isoformat(),
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
                    "cutoff_date": cutoff_date.isoformat(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document cleanup failed: {str(e)}",
        )


@router.get("/documents/stats", response_model=DocumentStatsResponse)
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
        total_size = (
            await db.scalar(
                select(func.sum(Document.file_size)).where(
                    Document.file_size.is_not(None)
                )
            )
            or 0
        )

        # File type distribution
        file_types = await db.execute(
            select(
                func.lower(func.split_part(Document.file_name, ".", -1)).label(
                    "extension"
                ),
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
                {
                    "extension": row.extension,
                    "count": row.count,
                    "total_size_bytes": row.total_size or 0,
                }
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
                select(func.count(Document.id)).where(
                    Document.created_at >= seven_days_ago
                )
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
                {
                    "username": row.username,
                    "document_count": row.document_count,
                    "total_size_bytes": row.total_size or 0,
                }
            )

        # Calculate success rate
        total_processed = status_counts.get("completed", 0) + status_counts.get(
            "failed", 0
        )
        success_rate = (
            status_counts.get("completed", 0) / max(total_processed, 1)
        ) * 100

        return {
            "success": True,
            "data": {
                "counts_by_status": status_counts,
                "total_documents": sum(status_counts.values()),
                "storage": {
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / 1024 / 1024, 2),
                    "avg_file_size_bytes": round(
                        total_size / max(sum(status_counts.values()), 1), 2
                    ),
                },
                "file_types": file_type_stats,
                "processing": {
                    "success_rate": round(success_rate, 2),
                    "avg_processing_time_seconds": round(avg_processing_time, 2),
                    "total_processed": total_processed,
                },
                "recent_activity": {
                    "uploads_last_7_days": recent_uploads,
                    "processed_last_7_days": recent_processed,
                },
                "top_uploaders": top_users,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document statistics: {str(e)}",
        )


@router.post("/documents/bulk-reprocess", response_model=BaseResponse)
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
    log_api_call(
        "bulk_reprocess_documents",
        user_id=str(current_user.id),
        status_filter=status_filter,
        limit=limit,
    )

    try:
        # Validate status filter
        status_map = {"failed": FileStatus.FAILED, "completed": FileStatus.COMPLETED}

        if status_filter not in status_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Use one of: {list(status_map.keys())}",
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
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Reprocess documents
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

        return {
            "success": True,
            "message": f"Bulk reprocessing initiated for {reprocessed_count} documents",
            "reprocessed_count": reprocessed_count,
            "total_found": len(documents),
            "errors": errors[:5],  # Limit error reporting
            "criteria": {"status_filter": status_filter, "limit": limit},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk reprocessing failed: {str(e)}",
        )


@router.get("/documents/search/advanced", response_model=AdvancedSearchResponse)
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD",
                )

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                filters.append(Document.created_at < date_to_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD",
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
            user_result = await db.execute(select(User).where(User.id == doc.user_id))
            user = user_result.scalar_one_or_none()

            results.append(
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "file_name": doc.file_name,
                    "file_size": doc.file_size,
                    "status": doc.status.value,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": (
                        doc.updated_at.isoformat() if doc.updated_at else None
                    ),
                    "user": {
                        "username": user.username if user else "Unknown",
                        "email": user.email if user else "Unknown",
                    },
                    "error_message": doc.error_message,
                }
            )

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
                    "limit": limit,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search failed: {str(e)}",
        )
