"""Document and document chunk database models.

This module defines SQLAlchemy models for document storage and processing,
including document metadata, processing status, and text chunks for vector search.
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, BigInteger, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModelDB

if TYPE_CHECKING:
    from app.models.user import User


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
    """Document model for storing uploaded files and their metadata.

    Stores information about uploaded documents including their content,
    processing status, and associated chunks for vector search.

    Attributes:
        title (Mapped[str]): Document title or filename.
        filename (Mapped[str]): Original filename.
        file_path (Mapped[Optional[str]]): Path to stored file.
        file_size (Mapped[int]): File size in bytes.
        file_type (Mapped[FileType]): Type of document.
        mime_type (Mapped[Optional[str]]): MIME type of the document.
        status (Mapped[FileStatus]): Processing status.
        metainfo (Mapped[Optional[Dict[str, Any]]]): Additional metadata.
        content (Mapped[Optional[str]]): Extracted text content.
        summary (Mapped[Optional[str]]): AI-generated summary.
        chunk_count (Mapped[int]): Number of text chunks created.
        processing_time (Mapped[Optional[float]]): Processing time in seconds.
        error_message (Mapped[Optional[str]]): Error message if processing failed.
        owner_id (Mapped[int]): ID of user who uploaded the document.
        owner (relationship): User who uploaded this document.
        chunks (relationship): Text chunks from this document.

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

    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="MIME type of the document"
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
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
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

    # Table arguments for indexes
    __table_args__ = (
        # Performance indexes
        Index("idx_documents_owner_id", "owner_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_file_type", "file_type"),
        Index("idx_documents_created_at", "created_at"),
        Index("idx_documents_updated_at", "updated_at"),
        # Composite indexes for common queries
        Index("idx_documents_owner_status", "owner_id", "status"),
        Index("idx_documents_owner_type", "owner_id", "file_type"),
        Index("idx_documents_owner_created", "owner_id", "created_at"),
        Index("idx_documents_status_created", "status", "created_at"),
        # Search indexes
        Index("idx_documents_title", "title"),
        Index("idx_documents_filename", "filename"),
    )

    def __repr__(self) -> str:
        """Return string representation of Document.

        Returns:
            str: String representation including ID, title, and status.

        """
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"


class DocumentChunk(BaseModelDB):
    """Document chunk model for storing text segments with embeddings.

    Stores individual text chunks from documents along with their vector
    embeddings for semantic search capabilities.

    Attributes:
        content (Mapped[str]): Text content of the chunk.
        chunk_index (Mapped[int]): Index of this chunk within the document.
        start_offset (Mapped[Optional[int]]): Starting character offset in original document.
        end_offset (Mapped[Optional[int]]): Ending character offset in original document.
        embedding (Mapped[Optional[List[float]]]): Vector embedding for semantic search.
        embedding_model (Mapped[Optional[str]]): Model used to generate embedding.
        token_count (Mapped[Optional[int]]): Number of tokens in this chunk.
        language (Mapped[Optional[str]]): Detected language of the chunk.
        document_id (Mapped[int]): ID of the parent document.
        document (relationship): Parent document for this chunk.

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
        Vector(3072),
        nullable=True,
        doc="Vector embedding for semantic search",
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
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of the parent document",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="chunks", doc="Parent document for this chunk"
    )

    # Table arguments for indexes
    __table_args__ = (
        # Performance indexes
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_chunk_index", "chunk_index"),
        Index("idx_chunks_created_at", "created_at"),
        # Composite indexes for common queries
        Index("idx_chunks_document_index", "document_id", "chunk_index"),
        Index("idx_chunks_document_created", "document_id", "created_at"),
        # Search and filtering indexes
        Index("idx_chunks_token_count", "token_count"),
        Index("idx_chunks_language", "language"),
        Index("idx_chunks_embedding_model", "embedding_model"),
        # Index("idx_embedding_vector_cosine", "embedding",
        #    postgresql_using="ivfflat",
        #    postgresql_with={"lists": 100},
        #    postgresql_ops={"embedding": "vector_cosine_ops"}
        # ),
    )

    def __repr__(self) -> str:
        """Return string representation of DocumentChunk.

        Returns:
            str: String representation including ID, document ID, and chunk index.

        """
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
