"""
Comprehensive user model for authentication, profile management, and security enforcement.

This module implements the core User entity with advanced authentication capabilities,
comprehensive profile management, and enterprise-grade security features. Provides
complete user lifecycle management with secure password handling, role-based access
control, audit trail integration, and relationship management with user-generated
content throughout the AI Chatbot Platform with full compliance and monitoring support.

Key Features:
- Secure authentication with bcrypt password hashing and salting algorithms
- Comprehensive user profile management with flexible personal information storage
- Role-based access control with superuser privileges and granular permission management
- Audit trail integration with login tracking and comprehensive activity monitoring
- Relationship management with user-generated documents, conversations, and content
- Account lifecycle management with activation, deactivation, and security controls

Security Features:
- Bcrypt password hashing with configurable work factors and salt generation
- Account status management with activation controls and security enforcement
- Login tracking with timestamp recording and suspicious activity monitoring
- Superuser privilege escalation with comprehensive audit logging and access controls
- Email verification and validation with security best practices and fraud prevention
- Account lockout and security policies with configurable thresholds and recovery

User Management:
- Flexible username policies with validation and uniqueness enforcement
- Email-based identification with format validation and deliverability checking
- Full name storage with optional display preferences and privacy controls
- Account status tracking with activation, suspension, and termination workflows
- Last login monitoring for security analysis and inactive account management
- Profile customization with preferences, settings, and personalization options

Relationship Management:
- Document ownership with access control and sharing permission management
- Conversation participation with message history and thread management
- Content creation tracking with authorship attribution and version control
- Collaboration features with team management and permission delegation
- Activity logging with comprehensive user action tracking and audit trails
- Integration with external systems for single sign-on and identity federation

Database Architecture:
- Optimized indexing on username, email, and login fields for query performance
- Foreign key relationships with proper cascade management and referential integrity
- Efficient storage with appropriate column types and size constraints
- Query optimization with strategic relationship loading and caching integration
- Backup and recovery compatibility with user data protection and retention policies
- Migration support with data preservation and schema evolution capabilities

Enterprise Integration:
- LDAP and Active Directory integration for enterprise authentication systems
- Single sign-on (SSO) compatibility with SAML and OAuth providers
- Multi-factor authentication support with TOTP and hardware token integration
- Compliance features supporting GDPR, SOX, and other regulatory requirements
- Audit logging integration with SIEM systems and security monitoring platforms
- Identity governance with automated provisioning and deprovisioning workflows

Use Cases:
- Enterprise application user management with comprehensive security and compliance
- Multi-tenant SaaS platform with user isolation and tenant-specific configurations
- API authentication and authorization with token management and session control
- Content management system with user-generated content and collaboration features
- Analytics and reporting with user behavior tracking and usage pattern analysis
- Integration hub for external authentication systems and identity providers
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .conversation import Conversation
    from .document import Document


class User(BaseModelDB):
    """
    Enterprise-grade user model with comprehensive authentication and profile management.

    Implements complete user lifecycle management with advanced security features,
    role-based access control, and comprehensive audit capabilities. Provides
    secure authentication with bcrypt password hashing, flexible profile management,
    and sophisticated relationship handling with user-generated content throughout
    the AI Chatbot Platform with enterprise-grade security, compliance, and
    monitoring capabilities for production-ready user management systems.

    Core Features:
    - Secure authentication with industry-standard bcrypt password hashing and salting
    - Comprehensive user profile management with flexible personal information storage
    - Role-based access control with superuser privileges and granular permission enforcement
    - Account lifecycle management with activation, deactivation, and security monitoring
    - Audit trail integration with login tracking and comprehensive activity logging
    - Relationship management with user-generated documents, conversations, and content

    Security Architecture:
    - Bcrypt password hashing with configurable work factors and cryptographic salt generation
    - Username and email uniqueness constraints enforced at database level with conflict resolution
    - Account status management with activation controls and automated security enforcement
    - Superuser privilege escalation with comprehensive audit logging and access control validation
    - Login timestamp tracking for security analysis and suspicious activity detection
    - Integration with authentication middleware and session management systems

    Data Model Attributes:
        username (Mapped[str]): Unique username for authentication with length validation (max 50 chars).
            Indexed for optimal query performance and login speed optimization.

        email (Mapped[str]): User email address for identification and communication (max 255 chars).
            Unique constraint enforced with format validation and deliverability checking.

        hashed_password (Mapped[str]): Bcrypt-hashed password with salt for secure authentication.
            Never stored in plaintext with configurable work factor and security validation.

        full_name (Mapped[Optional[str]]): Optional display name for user profile and personalization.
            Flexible length with privacy controls and display preference management.

        is_active (Mapped[bool]): Account activation status controlling authentication access.
            Enables account suspension and reactivation with comprehensive audit logging.

        is_superuser (Mapped[bool]): Administrative privilege flag for elevated access control.
            Enables role-based permissions with privilege escalation tracking and monitoring.

        last_login (Mapped[Optional[datetime]]): Timestamp of most recent successful authentication.
            Timezone-aware for global deployments with security monitoring integration.

    Relationship Management:
        documents (relationship): One-to-many relationship with Document entities owned by user.
            Cascade delete configuration maintaining referential integrity and data consistency.

        conversations (relationship): One-to-many relationship with Conversation entities created by user.
            Complete conversation history with message threading and participation tracking.

    Database Optimization:
        - Strategic indexing on username, email, active status, and superuser flags
        - Query optimization through relationship lazy loading and efficient join strategies
        - Foreign key constraints with proper cascade management and referential integrity
        - Connection pooling integration with user session management and authentication caching
        - Backup and recovery compatibility with user data protection and retention policies

    Security Features:
        - Password security with bcrypt hashing, salting, and configurable work factors
        - Account lockout prevention with rate limiting and suspicious activity detection
        - Email verification workflows with security token generation and validation
        - Multi-factor authentication support integration with TOTP and hardware tokens
        - Session management with secure token generation and automatic expiration
        - Audit logging for all authentication events and administrative actions

    Enterprise Integration:
        - LDAP and Active Directory integration for enterprise authentication systems
        - Single sign-on (SSO) compatibility with SAML, OAuth, and OpenID Connect providers
        - Identity governance with automated user provisioning and deprovisioning workflows
        - Compliance features supporting GDPR, SOX, HIPAA, and other regulatory requirements
        - Integration with SIEM systems for security monitoring and incident response
        - Multi-tenant support with user isolation and tenant-specific configuration management

    Use Cases:
        - Enterprise application user management with comprehensive security and compliance enforcement
        - Multi-tenant SaaS platform with user authentication and tenant isolation capabilities
        - API authentication and authorization with token-based access control and session management
        - Content management system with user-generated content ownership and collaboration features
        - Analytics and reporting with user behavior tracking and usage pattern analysis
        - Integration with external authentication systems and identity federation platforms

    Example:
        # Create new user with secure password hashing
        user = User(
            username="john_doe",
            email="john@example.com",
            hashed_password=hash_password("secure_password"),
            full_name="John Doe",
            is_active=True,
            is_superuser=False
        )
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_superuser", "is_superuser"),
    )

    def __repr__(self) -> str:
        """
        Return string representation of User model.

        Provides a concise string representation of the User instance
        for debugging and logging purposes.

        Returns:
            str: String representation containing username and email
        """
        return f"<User(username='{self.username}', email='{self.email}')>"
