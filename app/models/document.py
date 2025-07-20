"""
Document and document chunk database models.

This module defines SQLAlchemy models for document storage and processing,
including document metadata and text chunks for vector search.

Current Date and Time (UTC): 2025-07-14 05:03:11
Current User: lllucius
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB


class FileStatus(str, Enum):
    """Document processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class FileType(str, Enum):
    """Document type enumeration."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    HTML = "html"
    OTHER = "other"


class Document(BaseModelDB):
    """
    Document model for storing uploaded files and their metadata.

    This model stores information about uploaded documents including
    their content, processing status, and associated chunks.
    """

    __tablename__ = "documents"

    # Basic document information
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, doc="Document title or filename"
    )

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Original filename"
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, doc="Path to stored file"
    )

    content_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="MIME type of the document"
    )

    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="File size in bytes"
    )

    # File type and status
    file_type: Mapped[FileType] = mapped_column(
        SQLEnum(FileType),
        nullable=False,
        default=FileType.OTHER,
        doc="Type of document",
    )

    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus),
        nullable=False,
        default=FileStatus.PENDING,
        doc="Processing status",
    )

    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Content and processing
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Extracted text content"
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="AI-generated summary"
    )

    # Processing metadata
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of text chunks created"
    )

    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Processing time in seconds"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Error message if processing failed"
    )

    # User association
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of user who uploaded the document",
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="documents", doc="User who uploaded this document"
    )

    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        doc="Text chunks from this document",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"


class DocumentChunk(BaseModelDB):
    """
    Document chunk model for storing text segments with embeddings.

    This model stores individual text chunks from documents along with
    their vector embeddings for semantic search capabilities.
    """

    __tablename__ = "document_chunks"

    # Content information
    content: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Text content of the chunk"
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Index of this chunk within the document"
    )

    start_offset: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Starting character offset in original document"
    )

    end_offset: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Ending character offset in original document"
    )

    # Vector embedding
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(3072), nullable=True, doc="Vector embedding for semantic search"
    )

    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Model used to generate embedding"
    )

    # Metadata
    token_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Number of tokens in this chunk"
    )

    language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, doc="Detected language of the chunk"
    )

    # Document association
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of the parent document",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="chunks", doc="Parent document for this chunk"
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"