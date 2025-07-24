"Document model definitions and database schemas."

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    from pgvector.sqlalchemy import Vector

    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
from sqlalchemy import JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModelDB

if TYPE_CHECKING:
    from .user import User


class FileStatus(str, Enum):
    "FileStatus class for specialized functionality."

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class FileType(str, Enum):
    "FileType class for specialized functionality."

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    HTML = "html"
    OTHER = "other"


class Document(BaseModelDB):
    "Document data model for database operations."

    __tablename__ = "documents"
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
    metainfo: Mapped[Optional[Dict[(str, Any)]]] = mapped_column(JSON, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Extracted text content"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="AI-generated summary"
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of text chunks created"
    )
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Processing time in seconds"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Error message if processing failed"
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of user who uploaded the document",
    )
    owner: Mapped["User"] = relationship(
        "User", back_populates="documents", doc="User who uploaded this document"
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        doc="Text chunks from this document",
    )
    __table_args__ = (
        Index("idx_documents_owner_id", "owner_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_file_type", "file_type"),
        Index("idx_documents_created_at", "created_at"),
        Index("idx_documents_updated_at", "updated_at"),
        Index("idx_documents_owner_status", "owner_id", "status"),
        Index("idx_documents_owner_type", "owner_id", "file_type"),
        Index("idx_documents_owner_created", "owner_id", "created_at"),
        Index("idx_documents_status_created", "status", "created_at"),
        Index("idx_documents_title", "title"),
        Index("idx_documents_filename", "filename"),
    )

    def __repr__(self) -> str:
        "Return detailed object representation."
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"


class DocumentChunk(BaseModelDB):
    "DocumentChunk class for specialized functionality."

    __tablename__ = "document_chunks"
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
    if HAS_PGVECTOR:
        embedding: Mapped[Optional[List[float]]] = mapped_column(
            Vector(3072), nullable=True, doc="Vector embedding for semantic search"
        )
    else:
        embedding: Mapped[Optional[str]] = mapped_column(
            Text, nullable=True, doc="Vector embedding as JSON string for SQLite"
        )
    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Model used to generate embedding"
    )
    token_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Number of tokens in this chunk"
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, doc="Detected language of the chunk"
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of the parent document",
    )
    document: Mapped["Document"] = relationship(
        "Document", back_populates="chunks", doc="Parent document for this chunk"
    )
    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_chunk_index", "chunk_index"),
        Index("idx_chunks_created_at", "created_at"),
        Index("idx_chunks_document_index", "document_id", "chunk_index"),
        Index("idx_chunks_document_created", "document_id", "created_at"),
        Index("idx_chunks_token_count", "token_count"),
        Index("idx_chunks_language", "language"),
        Index("idx_chunks_embedding_model", "embedding_model"),
    )

    def __repr__(self) -> str:
        "Return detailed object representation."
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
