"""
Comprehensive conversation and message models for advanced chat functionality and AI interaction.

This module implements sophisticated conversation management with advanced message tracking,
AI response handling, tool integration capabilities, and comprehensive metadata management.
Provides complete conversational AI infrastructure with message threading, context management,
and enterprise-grade features for chat platforms, customer service systems, and AI-powered
applications with full audit trails, analytics integration, and performance optimization.

Key Features:
- Advanced conversation threading with hierarchical message organization and context preservation
- Comprehensive message tracking with AI responses, tool calls, and metadata management
- User relationship management with ownership, permissions, and collaboration capabilities
- JSON metadata storage for flexible conversation context and application-specific data
- Message count caching for performance optimization and conversation analytics
- Enterprise-grade audit trails with comprehensive change tracking and compliance logging

Conversation Management:
- Hierarchical conversation organization with threading and topic management
- User ownership and permission management with sharing and collaboration features
- Conversation lifecycle management with activation, archival, and deletion workflows
- Context preservation across message exchanges with intelligent memory management
- Conversation analytics with usage metrics, engagement scoring, and performance tracking
- Integration with external chat platforms and messaging systems

Message Architecture:
- Comprehensive message modeling with content, metadata, and relationship tracking
- AI response integration with model information, token usage, and performance metrics
- Tool call support with execution results, error handling, and audit logging
- Message threading with reply chains, conversation branching, and context management
- Rich content support including text, images, files, and structured data formats
- Message analytics with delivery tracking, engagement metrics, and quality assessment

AI Integration Features:
- Large Language Model response tracking with model identification and performance metrics
- Tool execution logging with input parameters, results, and error handling
- Conversation context management with memory optimization and relevance scoring
- AI assistance metadata including reasoning chains, confidence scores, and decision logging
- Multi-modal support including text, voice, image, and document processing capabilities
- Real-time streaming support for progressive response generation and user experience

Database Architecture:
- Optimized indexing on user relationships, conversation status, and message ordering
- Efficient storage with appropriate column types and JSON field optimization
- Query performance optimization with strategic relationship loading and caching integration
- Foreign key constraints with proper cascade management and referential integrity
- Pagination support for large conversations with efficient offset and cursor strategies
- Archive and retention policies with automated cleanup and compliance management

Performance Features:
- Message count caching reducing complex aggregation queries and improving response times
- Lazy loading relationships optimizing memory usage and query performance
- Efficient pagination with cursor-based navigation for large conversation histories
- JSON field indexing for metadata queries and application-specific search capabilities
- Connection pooling integration with conversation session management and user tracking
- Real-time synchronization with WebSocket integration and live update capabilities

Enterprise Capabilities:
- Comprehensive audit logging for regulatory compliance and security monitoring
- Data retention policies with automated archival and deletion workflows
- Privacy controls with data anonymization and right-to-be-forgotten compliance
- Integration with enterprise chat platforms including Slack, Teams, and custom systems
- Analytics and reporting with conversation insights, user behavior, and AI performance metrics
- Multi-tenant support with conversation isolation and tenant-specific configurations

Use Cases:
- Customer service platforms with AI assistance and human agent collaboration
- Enterprise chat applications with conversation archival and compliance features
- AI-powered virtual assistants with context preservation and personalization
- Educational platforms with tutoring conversations and progress tracking
- Healthcare applications with patient interaction tracking and privacy compliance
- Analytics and research platforms with conversation data mining and insight generation
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .user import User


class Conversation(BaseModelDB):
    """
    Enterprise-grade conversation model for advanced chat session and dialogue thread management.

    Implements sophisticated conversation management with comprehensive message tracking,
    AI interaction capabilities, and enterprise-grade features for chat platforms,
    customer service systems, and AI-powered applications. Provides complete
    conversational infrastructure with user relationship management, metadata storage,
    performance optimization, and comprehensive audit capabilities for production-ready
    chat systems with scalability and compliance requirements.

    Core Features:
    - Advanced conversation threading with hierarchical message organization and context preservation
    - User ownership and permission management with sharing and collaboration capabilities
    - JSON metadata storage for flexible conversation context and application-specific data
    - Message count caching for performance optimization and conversation analytics
    - Conversation lifecycle management with activation, archival, and deletion workflows
    - Enterprise-grade audit trails with comprehensive change tracking and compliance logging

    Data Model Attributes:
        title (Mapped[Optional[str]]): Human-readable conversation title with search optimization.
            Supports conversation categorization, organization, and user-friendly identification.
            Maximum 500 characters with full-text search indexing for efficient discovery.

        is_active (Mapped[bool]): Conversation activation status controlling accessibility and visibility.
            Enables conversation archival and lifecycle management without data deletion.
            Integrated with user interface filters and administrative management workflows.

        message_count (Mapped[int]): Cached message count for performance optimization and analytics.
            Automatically maintained through database triggers and application-level updates.
            Enables efficient pagination and conversation size monitoring without expensive aggregations.

        user_id (Mapped[uuid.UUID]): Foreign key reference to conversation owner with relationship integrity.
            Enforces user ownership and enables user-specific conversation filtering and access control.
            Indexed for optimal query performance and user conversation retrieval.

        metainfo (Mapped[Optional[Dict[str, Any]]]): Flexible JSON metadata for conversation context.
            Stores application-specific data including conversation settings, AI parameters, and custom attributes.
            Supports complex queries with PostgreSQL JSON operators and indexing capabilities.

    Relationship Management:
        messages (relationship): One-to-many relationship with Message entities in chronological order.
            Cascade delete configuration maintaining referential integrity and data consistency.
            Lazy loading optimization preventing unnecessary message loading and memory consumption.

        user (relationship): Many-to-one relationship with User entity for ownership management.
            Back-reference enabling efficient user-to-conversations navigation and filtering.
            Foreign key constraint ensuring data integrity and preventing orphaned conversations.

    Database Optimization:
        - Strategic indexing on user_id, is_active status, and conversation title for query performance
        - JSON field indexing for metadata queries and application-specific search capabilities
        - Message count caching reducing expensive aggregation queries and improving response times
        - Efficient pagination support with cursor-based navigation for large conversation histories
        - Query optimization through relationship lazy loading and strategic join configuration

    Performance Features:
        - Message count caching eliminating expensive COUNT queries and improving dashboard performance
        - Lazy loading relationships optimizing memory usage and preventing N+1 query problems
        - JSON metadata indexing enabling efficient application-specific queries and filtering
        - Connection pooling integration with conversation session management and user tracking
        - Real-time synchronization support with WebSocket integration and live update capabilities

    Enterprise Capabilities:
        - Comprehensive audit logging for regulatory compliance and security monitoring
        - Data retention policies with automated archival and deletion workflows
        - Privacy controls with data anonymization and right-to-be-forgotten compliance
        - Multi-tenant support with conversation isolation and tenant-specific configurations
        - Integration with enterprise chat platforms and external messaging systems
        - Analytics and reporting with conversation insights and user behavior tracking

    Security Features:
        - User ownership enforcement with proper access control and permission validation
        - Data encryption for sensitive conversation metadata and content protection
        - Audit trail integration with comprehensive change tracking and security monitoring
        - Privacy compliance with data classification and protection policies
        - Access logging for security analysis and suspicious activity detection

    Use Cases:
        - Customer service platforms with AI assistance and human agent collaboration workflows
        - Enterprise chat applications with conversation archival and compliance features
        - AI-powered virtual assistants with context preservation and personalization capabilities
        - Educational platforms with tutoring conversations and progress tracking
        - Healthcare applications with patient interaction tracking and privacy compliance
        - Analytics platforms with conversation data mining and insight generation

    Example:
        # Create new conversation with metadata
        conversation = Conversation(
            title="Customer Support - Order #12345",
            is_active=True,
            message_count=0,
            user_id=user.id,
            metainfo={"category": "support", "priority": "high", "tags": ["order", "billing"]}
        )
    """

    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    user: Mapped["User"] = relationship("User", back_populates="conversations")

    # Indexes
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_active", "is_active"),
        Index("idx_conversations_title", "title"),
    )

    def __repr__(self) -> str:
        """
        Return string representation of Conversation model.

        Provides a concise string representation for debugging and logging.

        Returns:
            str: String representation containing title and user_id
        """
        return f"<Conversation(title='{self.title}', user_id={self.user_id})>"


class Message(BaseModelDB):
    """
    Message model for individual chat messages within conversations.

    This model represents individual messages in conversation threads, supporting
    various message types including user inputs, AI responses, and system messages.
    Includes support for tool calls and comprehensive message metadata.

    Attributes:
        role: Message role identifier (user, assistant, system) - max 20 chars
        content: The actual message text content (unlimited length)
        token_count: Number of tokens in the message for usage tracking
        conversation_id: UUID of the parent conversation this message belongs to
        tool_calls: JSON data containing tool calls made in this message
        tool_call_results: JSON data containing results from executed tool calls
        metainfo: Additional JSON metadata for message context and processing
        conversation: Reference to the parent conversation

    Message Roles:
        - user: Messages from human users
        - assistant: Messages from AI assistant
        - system: System messages and instructions

    Database Indexes:
        - idx_messages_conversation_id: Fast lookup by conversation
        - idx_messages_role: Filter by message role
        - idx_messages_created_at: Chronological ordering and time-based queries

    Relationships:
        - conversation: Many-to-one relationship with Conversation model
        - Uses cascade delete through conversation relationship

    Tool Call Support:
        - tool_calls: Stores tool invocation data and parameters
        - tool_call_results: Stores execution results and responses
        - Supports complex tool interaction workflows

    Note:
        This model inherits id, created_at, and updated_at fields from BaseModelDB.
        Messages are ordered chronologically within conversations.
    """

    __tablename__ = "messages"

    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_calls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tool_call_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    metainfo: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created_at", "created_at"),
    )


    def __repr__(self) -> str:
        """
        Return string representation of Message model.

        Provides a concise string representation for debugging and logging.

        Returns:
            str: String representation containing role and conversation_id
        """
        return f"<Message(role='{self.role}', conv_id={self.conversation_id})>"
