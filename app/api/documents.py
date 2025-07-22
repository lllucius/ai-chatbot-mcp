"""
Document management API endpoints.

This module provides endpoints for document upload, processing,
management, and retrieval operations.

Generated on: 2025-07-14 03:12:05 UTC
Current User: lllucius
"""

from typing import Optional

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
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..config import settings
from ..core.exceptions import DocumentError, NotFoundError, ValidationError
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse, PaginatedResponse
from ..schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
    ProcessingStatusResponse,
    ProcessingConfigResponse,
    BackgroundTaskResponse,
)
from ..services.document import DocumentService
from ..services.background_processor import get_background_processor
from ..utils.api_errors import handle_api_errors

router = APIRouter(tags=["documents"])


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)


@router.post("/upload", response_model=DocumentUploadResponse)
@handle_api_errors("Failed to upload document", log_errors=True)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    auto_process: bool = Form(default=True),
    processing_priority: int = Form(default=5, ge=1, le=10),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """
    Upload a document for processing.

    Enhanced with auto-processing option and priority control.
    """
    try:
        # Create document
        document = await service.create_document(file, title, user.id)

        task_id = None
        if auto_process:
            # Start background processing
            task_id = await service.start_processing(
                document.id, priority=processing_priority
            )

        return DocumentUploadResponse(
            message="Document uploaded successfully",
            document=DocumentResponse.model_validate(document),
            task_id=task_id,
            auto_processing=auto_process,
        )

    except (ValidationError, DocumentError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed"
        )


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
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
    """
    try:
        documents, total = await document_service.list_documents(
            user_id=current_user.id,
            page=page,
            size=size,
            file_type=file_type,
            status_filter=status_filter,
        )

        document_responses = [DocumentResponse.model_validate(doc) for doc in documents]

        return PaginatedResponse.create(
            items=document_responses,
            total=total,
            page=page,
            size=size,
            message="Documents retrieved successfully",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get document by ID.

    Returns detailed information about a specific document
    owned by the current user.
    """
    try:
        document = await document_service.get_document(document_id, current_user.id)
        return DocumentResponse.model_validate(document)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document",
        )


@router.put("/{document_id}", response_model=DocumentResponse)
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
    """
    try:
        document = await document_service.update_document(
            document_id, request, current_user.id
        )
        return DocumentResponse.model_validate(document)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document update failed",
        )


@router.delete("/{document_id}", response_model=BaseResponse)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Delete document and all associated data.

    Permanently deletes the document, its chunks, embeddings,
    and removes the file from storage.
    """
    try:
        success = await document_service.delete_document(document_id, current_user.id)

        if success:
            return BaseResponse(success=True, message="Document deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document deletion failed",
        )


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get document processing status.

    Returns current processing status, progress, and any error information
    for the specified document.
    """
    try:
        status_info = await document_service.get_processing_status(
            document_id, current_user.id
        )

        return ProcessingStatusResponse(
            success=True, message="Processing status retrieved", **status_info
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve processing status",
        )


@router.post("/{document_id}/reprocess", response_model=BaseResponse)
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
    """
    try:
        success = await document_service.reprocess_document(
            document_id, current_user.id
        )

        if success:
            return BaseResponse(success=True, message="Document reprocessing started")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reprocess document at this time",
            )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reprocessing failed",
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Download original document file.

    Returns the original uploaded file for download.
    """
    try:
        file_path, filename, mime_type = await document_service.get_download_info(
            document_id, current_user.id
        )

        from fastapi.responses import FileResponse

        return FileResponse(path=file_path, filename=filename, media_type=mime_type)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Download failed"
        )


@router.post("/{document_id}/process", response_model=BackgroundTaskResponse)
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
    """
    try:
        task_id = await service.start_processing(document_id, priority=priority)

        return BackgroundTaskResponse(
            message="Document processing started",
            task_id=task_id,
            document_id=str(document_id),
            status="queued",
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{document_id}/enhanced-status", response_model=ProcessingStatusResponse)
@handle_api_errors("Failed to get processing status", log_errors=True)
async def get_enhanced_processing_status(
    document_id: UUID,
    task_id: Optional[str] = Query(
        None, description="Optional task ID for background processing details"
    ),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> ProcessingStatusResponse:
    """
    Get comprehensive document processing status with background task information.

    Includes both document status and background task progress details.
    """
    try:
        status_info = await service.get_processing_status(document_id, task_id)

        return ProcessingStatusResponse(
            message="Enhanced processing status retrieved", **status_info
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )


@router.get("/processing-config", response_model=ProcessingConfigResponse)
async def get_processing_config() -> ProcessingConfigResponse:
    """
    Get current document processing configuration.

    Returns the current settings for chunk sizes, overlaps, and other processing parameters.
    """
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


@router.get("/queue-status")
@handle_api_errors("Failed to get queue status", log_errors=True)
async def get_queue_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get background processing queue status.

    Provides information about current queue size, active tasks, and processing capacity.
    """
    background_processor = await get_background_processor(db)
    queue_status = await background_processor.get_queue_status()

    return {"message": "Queue status retrieved", **queue_status}
