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
)
from ..services.document import DocumentService
from ..utils.api_errors import handle_api_errors

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)


@router.post("/upload", response_model=DocumentUploadResponse)
@handle_api_errors("Failed to upload document", log_errors=True)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Upload a new document for processing.

    Supports PDF, DOCX, TXT, MD, RTF files up to the configured size limit.
    The document will be processed asynchronously for text extraction and chunking.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Check file type
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_extension}' not supported. Allowed types: {', '.join(settings.allowed_file_types)}",
            )

        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed ({settings.max_file_size} bytes)",
            )

        # Reset file position
        await file.seek(0)

        # Use filename as title if not provided
        if not title:
            title = file.filename

        # Create document record and save file
        document = await document_service.create_document(
            file=file, title=title, user_id=current_user.id
        )

        # Start processing (this should be async in production)
        processing_started = await document_service.start_processing(document.id)

        return DocumentUploadResponse(
            success=True,
            message="Document uploaded successfully",
            document=DocumentResponse.model_validate(document),
            processing_started=processing_started,
            estimated_completion="Processing will complete within a few minutes",
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed",
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
