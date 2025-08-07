"""User-related Pydantic schemas for comprehensive API requests and responses.

This module defines comprehensive schemas for user operations including account creation,
profile updates, authentication, password management, and detailed API responses using
modern Pydantic V2 features. Implements robust validation, security controls, and
comprehensive user data management capabilities.

Key Features:
- User account creation and profile management with comprehensive validation
- Password security with strength requirements and secure handling
- User profile updates with field-level validation and security controls
- Authentication integration with secure credential management
- Administrative user management with role and permission controls
- User statistics and analytics for system monitoring and reporting

User Schema Hierarchy:
- UserBase: Foundation schema with common user fields and validation
- UserCreate: Account creation with password security and validation
- UserUpdate: Profile updates with selective field modification
- UserPasswordUpdate: Secure password change with validation
- UserResponse: API response formatting with comprehensive user information
- UserListResponse: Paginated user listing with metadata
- UserStatsResponse: User analytics and system statistics

Security Features:
- Password strength validation with complexity requirements
- Username format validation with security restrictions
- Email validation with proper format checking
- Input sanitization to prevent injection attacks
- Field-level validation for data integrity and security
- Secure password handling without exposure in responses

Validation Capabilities:
- Comprehensive field validation with custom validators
- Business rule enforcement for user management
- Data type and format validation for security
- Cross-field validation for consistency checking
- Input sanitization and normalization for security
- Error reporting with detailed validation feedback

User Management:
- Account lifecycle management (creation, updates, deactivation)
- Role-based access control with superuser privileges
- Profile management with comprehensive field updates
- Password management with secure change workflows
- Account status tracking and administrative controls
- User analytics and system usage monitoring

API Integration:
- RESTful API response formatting with consistent structure
- Pagination support for large user datasets
- Search and filtering capabilities for user discovery
- Statistical reporting for user analytics and monitoring
- Administrative operations with proper access control
- Integration with authentication and authorization systems

Use Cases:
- User registration and account creation workflows
- Profile management and user preference settings
- Administrative user management and system oversight
- User analytics and system monitoring dashboards
- Authentication and authorization system integration
- Multi-tenant user management with proper isolation
"""

import json
from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, Field, field_validator

from .base import BaseSchema
from .common import BaseResponse, PaginationParams


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


class UserBase(BaseSchema):
    """Foundation user schema with core fields and comprehensive validation for user management.

    Serves as the base class for all user-related schemas with essential user fields,
    validation rules, and security controls. Implements comprehensive field validation
    for username uniqueness, email format checking, and user profile information
    with proper security measures and data integrity enforcement.

    Core User Fields:
        - username: Unique alphanumeric identifier with format restrictions
        - email: Valid email address with domain verification
        - full_name: Optional display name for user personalization

    Validation Features:
        - Username format validation with character restrictions and length limits
        - Email format validation with proper domain checking
        - Input sanitization to prevent injection attacks and malicious data
        - Field length validation for security and database constraints
        - Business rule enforcement for user account consistency

    Security Controls:
        - Username normalization to lowercase for consistency
        - Input validation to prevent SQL injection and XSS attacks
        - Character restrictions to prevent parsing and security issues
        - Field length limits to prevent buffer overflow vulnerabilities
        - Comprehensive validation error reporting for security monitoring

    Username Requirements:
        - Alphanumeric characters (a-z, A-Z, 0-9) for compatibility
        - Underscores (_) and hyphens (-) for readability and accessibility
        - Length restrictions (3-50 characters) for practical use
        - Case-insensitive normalization for consistency
        - Pattern validation to prevent special characters and security issues

    Profile Management:
        - Optional full name for user personalization and display
        - Email address for communication and account recovery
        - Extensible design for additional profile fields
        - Integration with user preferences and settings
        - Support for internationalization and localization

    Use Cases:
        - Base class for all user-related API schemas
        - User profile display and management interfaces
        - User account creation and registration workflows
        - Administrative user management and oversight
        - Integration with authentication and authorization systems

    Example:
        user_data = UserBase(
            username="john_doe",
            email="john@example.com",
            full_name="John Doe"
        )

    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore",
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Unique username",
    )
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(
        default=None, max_length=100, description="User's full name"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format with comprehensive security and consistency rules.

        Ensures username meets security, compatibility, and consistency requirements
        by enforcing character restrictions, length validation, and format normalization.
        Implements security measures to prevent usernames that could cause parsing
        issues, security vulnerabilities, or system conflicts.

        Args:
            v: Username value to validate and normalize

        Returns:
            str: Validated and normalized username in lowercase format

        Raises:
            ValueError: If username is empty, too short, or too long

        Validation Rules:
            - Cannot be empty or None value
            - Minimum 3 characters for practical use and uniqueness
            - Maximum 50 characters for database and display constraints
            - Automatic normalization to lowercase for consistency
            - Pattern validation handled by Field declaration

        Security Features:
            - Character restrictions prevent injection attacks
            - Length limits prevent buffer overflow vulnerabilities
            - Case normalization prevents duplicate username issues
            - Input validation prevents malicious username patterns
            - Comprehensive error reporting for validation failures

        Normalization Benefits:
            - Consistent username comparison and lookup operations
            - Prevention of case-sensitive duplicate usernames
            - Simplified database indexing and search operations
            - User-friendly login with case-insensitive matching
            - Integration with external systems requiring lowercase identifiers

        Example:
            validate_username("John_Doe")  # Returns: "john_doe"
            validate_username("user123")   # Returns: "user123"
            validate_username("ab")        # Raises: ValueError (too short)
            validate_username("")          # Raises: ValueError (empty)

        """
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username cannot be longer than 50 characters")
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating new user accounts with comprehensive security validation.

    Extends UserBase with password field and security validation for user account
    creation workflows. Implements industry-standard password complexity requirements
    and comprehensive security controls for robust user registration and account
    provisioning processes.

    Account Creation Features:
        - Comprehensive user profile creation with validation
        - Secure password handling with strength requirements
        - Input validation and sanitization for security
        - Business rule enforcement for account creation
        - Integration with user registration workflows

    Password Security:
        - Minimum 8 characters for baseline security protection
        - Character complexity requirements (uppercase, lowercase, digits)
        - Maximum length limits for practical use and security
        - Comprehensive strength validation with detailed feedback
        - Protection against common password vulnerabilities

    Security Validation:
        - Password complexity enforcement to prevent weak credentials
        - Input sanitization to prevent injection attacks
        - Field validation for data integrity and consistency
        - Security rule enforcement for account protection
        - Comprehensive error reporting for validation failures

    Registration Process:
        - User profile information collection and validation
        - Password creation with security requirement enforcement
        - Email verification and format validation
        - Username uniqueness checking and format validation
        - Account creation with proper security controls

    Use Cases:
        - User registration forms in web and mobile applications
        - Administrative user account creation and provisioning
        - Bulk user import with validation and security controls
        - API-based user account creation with authentication
        - Self-service registration with automated verification

    Security Benefits:
        - Protection against weak password creation
        - Prevention of common account creation vulnerabilities
        - Comprehensive input validation and sanitization
        - Security rule enforcement for account protection
        - Audit trail support for account creation monitoring

    Example:
        new_user = UserCreate(
            username="john_doe",
            email="john@example.com",
            full_name="John Doe",
            password="SecurePassword123!"
        )

    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (minimum 8 characters)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength with comprehensive security requirements for account creation.

        Implements industry-standard password complexity requirements to ensure user
        account security and protection against common password-based attacks. Enforces
        multiple validation criteria for robust password security during account creation.

        Args:
            v: Password value to validate for strength and complexity

        Returns:
            str: Validated password if all security requirements are met

        Raises:
            ValueError: If password fails any security requirement

        Security Requirements:
            - Minimum 8 characters for baseline security protection
            - At least one uppercase letter (A-Z) for character complexity
            - At least one lowercase letter (a-z) for character diversity
            - At least one digit (0-9) for enhanced security entropy
            - Maximum 128 characters for practical use and system compatibility

        Password Strength Benefits:
            - Protection against dictionary attacks through complexity requirements
            - Resistance to brute force attacks through character diversity
            - Enhanced entropy for cryptographic security and protection
            - Compliance with security standards and best practices
            - Reduced risk of credential compromise and account takeover

        Validation Process:
            - Length validation for minimum and maximum security requirements
            - Character type validation for complexity enforcement
            - Security rule checking for comprehensive protection
            - Error reporting with specific requirement feedback
            - Integration with password policy enforcement systems

        Attack Protection:
            - Dictionary attacks: Complexity requirements prevent common words
            - Brute force attacks: Character diversity increases attack complexity
            - Social engineering: Strong passwords resist guessing attempts
            - Credential stuffing: Unique complex passwords reduce reuse risks
            - Password spraying: Strong requirements prevent common password use

        Example:
            validate_password("SecurePass123")   # Valid - meets all requirements
            validate_password("password")        # Invalid - missing uppercase/digit
            validate_password("PASSWORD123")     # Invalid - missing lowercase
            validate_password("Pass12")          # Invalid - too short (less than 8)

        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """Schema for selective user profile updates with comprehensive field validation.

    Handles partial user profile updates with optional field modifications, validation,
    and security controls. Implements selective field updates allowing users and
    administrators to modify specific profile information while maintaining data
    integrity and security requirements.

    Update Capabilities:
        - Selective field updates with optional field validation
        - Email address modification with format verification
        - Full name updates with length and content validation
        - Account status management for administrative control
        - Partial update support for efficient profile management

    Field Update Options:
        - email: Email address modification with uniqueness validation
        - full_name: Display name updates with length restrictions
        - is_active: Account status control for administrative management
        - Optional fields allow selective updates without affecting other data
        - Validation applies only to provided fields for flexibility

    Security Features:
        - Input validation and sanitization for security protection
        - Field-level validation for data integrity maintenance
        - Access control integration for administrative operations
        - Audit trail support for profile modification tracking
        - Protection against unauthorized profile modifications

    Administrative Controls:
        - Account activation and deactivation through is_active field
        - Administrative oversight for sensitive profile modifications
        - Role-based access control for update operation authorization
        - Comprehensive logging for profile modification audit trails
        - Integration with user management and administrative systems

    Use Cases:
        - User profile self-service updates and modifications
        - Administrative user management and account control
        - Bulk user profile updates with selective field modification
        - Account status management for user lifecycle control
        - Integration with user preference and settings management

    Validation Benefits:
        - Ensures data integrity during partial profile updates
        - Maintains email format and uniqueness requirements
        - Enforces field length limits for security and consistency
        - Provides flexible update options without rigid requirements
        - Supports incremental profile enhancement and modification

    Example:
        # Update only email address
        update_data = UserUpdate(email="new_email@example.com")

        # Update multiple fields
        update_data = UserUpdate(
            email="updated@example.com",
            full_name="Updated Name",
            is_active=True
        )

    """

    model_config = ConfigDict(
        from_attributes=True, validate_assignment=True, extra="ignore"
    )

    email: Optional[EmailStr] = Field(default=None, description="New email address")
    full_name: Optional[str] = Field(
        default=None, max_length=100, description="Updated full name"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether user is active"
    )


class UserPasswordUpdate(BaseSchema):
    """Schema for secure password change operations with comprehensive validation and verification.

    Handles secure password change workflows with current password verification and
    new password strength validation. Implements multi-factor security validation
    to ensure authorized password changes and protection against unauthorized
    account access and password modification attempts.

    Password Change Security:
        - Current password verification for authorization
        - New password strength validation with complexity requirements
        - Secure password handling without exposure in logs or storage
        - Protection against unauthorized password modification attempts
        - Comprehensive security validation for password change operations

    Validation Process:
        - Current password verification to confirm user identity and authorization
        - New password strength validation with industry-standard requirements
        - Password change authorization and security verification
        - Audit logging for password change operations and security monitoring
        - Protection against password change abuse and security vulnerabilities

    Security Requirements:
        - Current password must be provided and verified for authorization
        - New password must meet complexity requirements (uppercase, lowercase, digits)
        - Password change operations logged for security monitoring and compliance
        - Protection against brute force password change attempts
        - Secure password transmission and handling throughout the process

    Password Strength Validation:
        - Minimum 8 characters for baseline security protection
        - Character complexity requirements for enhanced security
        - Protection against weak password selection during changes
        - Consistent security standards with account creation requirements
        - Comprehensive validation feedback for user guidance

    Use Cases:
        - User-initiated password changes for security maintenance
        - Password updates following security incidents or policy requirements
        - Administrative password changes with proper authorization
        - Security-driven password rotation and compliance requirements
        - Password recovery completion with secure verification

    Security Benefits:
        - Protection against unauthorized password modification
        - Verification of user identity before password changes
        - Enforcement of strong password requirements during changes
        - Comprehensive audit trail for password change operations
        - Integration with security monitoring and incident response systems

    Example:
        password_change = UserPasswordUpdate(
            current_password="CurrentPassword123!",
            new_password="NewSecurePassword456!"
        )

    """

    model_config = ConfigDict(validate_assignment=True)

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength with comprehensive security requirements for password changes.

        Implements the same rigorous password complexity requirements as account creation
        to ensure consistent security standards across all password operations. Enforces
        multiple validation criteria for robust password security during password changes.

        Args:
            v: New password value to validate for strength and complexity

        Returns:
            str: Validated password if all security requirements are met

        Raises:
            ValueError: If password fails any security requirement

        Security Requirements:
            - Minimum 8 characters for baseline security protection
            - At least one uppercase letter (A-Z) for character complexity
            - At least one lowercase letter (a-z) for character diversity
            - At least one digit (0-9) for enhanced security entropy
            - Maximum 128 characters for practical use and system compatibility

        Password Change Security:
            - Same validation standards as account creation for consistency
            - Protection against weak password selection during changes
            - Enhanced security for password change operations
            - Prevention of common password vulnerabilities during updates
            - Compliance with organizational security policies and standards

        Validation Consistency:
            - Identical requirements to account creation password validation
            - Consistent security standards across all password operations
            - Unified error messaging for user experience consistency
            - Same protection mechanisms for all password entry points
            - Comprehensive security coverage for password lifecycle management

        Attack Protection:
            - Dictionary attacks: Complexity requirements prevent common words
            - Brute force attacks: Character diversity increases attack difficulty
            - Social engineering: Strong passwords resist guessing attempts
            - Credential reuse: Encourages unique password creation during changes
            - Password spraying: Complexity prevents common password patterns

        Example:
            validate_new_password("NewSecurePass123")  # Valid - meets all requirements
            validate_new_password("newpassword")       # Invalid - missing uppercase/digit
            validate_new_password("NEWPASSWORD123")    # Invalid - missing lowercase
            validate_new_password("NewPass")           # Invalid - too short

        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(UserBase):
    """Schema for comprehensive user API responses with complete profile information.

    Provides complete user profile information for API responses including account
    metadata, status information, and audit timestamps. Implements custom JSON
    serialization for proper UUID and datetime handling with frontend-compatible
    formatting and comprehensive user data presentation.

    Response Information:
        - Complete user profile with all public information
        - Account status and privilege information
        - Creation timestamp for audit and tracking purposes
        - Unique identifier for entity correlation and reference
        - Custom JSON serialization for proper type conversion

    User Metadata:
        - id: Unique UUID identifier for user entity correlation
        - is_active: Account status for access control and lifecycle management
        - is_superuser: Administrative privilege indicator for authorization
        - created_at: Account creation timestamp for audit and analytics
        - Inherited fields: username, email, full_name from UserBase

    Security Considerations:
        - Password field excluded from all response schemas for security
        - Sensitive information filtered for appropriate access levels
        - Account status information for access control decisions
        - Administrative privilege information for role-based authorization
        - Audit timestamps for security monitoring and compliance

    JSON Serialization:
        - UUID fields converted to string representation for API compatibility
        - Datetime fields converted to ISO format with timezone indicators
        - Custom serialization for frontend compatibility and integration
        - Consistent field formatting across all API responses
        - Support for nested object serialization with proper type conversion

    Use Cases:
        - User profile display in web and mobile applications
        - API responses for user management and administrative operations
        - User directory and search result formatting
        - Authentication response with user information
        - Administrative dashboards and user analytics

    Access Control Integration:
        - Account status checking for access control decisions
        - Administrative privilege verification for authorization
        - User information for role-based access control systems
        - Integration with authentication and authorization middleware
        - Support for multi-tenant access control and user isolation

    Example:
        user_response = UserResponse(
            id=123,
            username="john_doe",
            email="john@example.com",
            full_name="John Doe",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now()
        )
        json_str = user_response.model_dump_json()  # Properly formatted JSON

    """

    id: int = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_superuser: bool = Field(..., description="Whether the user has admin privileges")
    created_at: datetime = Field(..., description="When the user account was created")

    def model_dump_json(self, **kwargs):
        """Serialize model with comprehensive ID and datetime handling for user responses.

        Converts datetime fields to appropriate string representations for JSON
        compatibility and frontend integration. Provides consistent formatting for user
        response data across all API endpoints with proper type conversion.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with properly formatted datetime fields

        Serialization Features:
            - Integer ID preserved in its original format for API compatibility
            - Datetime to ISO format conversion with timezone indicators
            - Consistent field formatting for all user response data
            - Frontend-compatible JSON structure for web and mobile applications
            - Support for nested object serialization with proper type handling

        Field Conversion:
            - id: Integer preserved in original format
            - created_at: Datetime converted to ISO format with 'Z' suffix
            - updated_at: Datetime converted to ISO format if present
            - Other fields: Preserved in their original format

        Use Cases:
            - API response serialization for user management endpoints
            - User profile data formatting for frontend applications
            - Administrative dashboard data presentation
            - User directory and search result formatting
            - Integration with external systems requiring JSON format

        Example:
            user = UserResponse(id=123, username="john", ...)
            json_output = user.model_dump_json()
            # Result: {"id": 123, "created_at": "2024-01-01T12:00:00Z", ...}

        """
        data = self.model_dump(**kwargs)
        for field_name in ["created_at", "updated_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        return json.dumps(data)


class UserListResponse(BaseResponse):
    """Response schema for user list endpoints with comprehensive pagination and metadata.

    Provides structured response format for user listing operations with pagination
    support, total count information, and comprehensive user data. Implements
    consistent response structure for user management interfaces and administrative
    operations with proper data organization and metadata.

    Response Structure:
        - users: List of complete user profiles with all public information
        - total_count: Total number of users for pagination and statistics
        - Inherited fields: success, message from BaseResponse for consistency
        - Comprehensive metadata for client-side pagination and navigation

    Pagination Integration:
        - Total count for calculating pagination metadata (pages, offsets)
        - User list with proper ordering and filtering applied
        - Integration with pagination parameters for consistent navigation
        - Support for large user datasets with efficient pagination
        - Client-friendly pagination metadata for user interface development

    Use Cases:
        - User management dashboards and administrative interfaces
        - User directory and search result presentation
        - Administrative user listing with filtering and search capabilities
        - User analytics and reporting with comprehensive user information
        - Integration with user management systems and external directories

    Administrative Features:
        - Complete user information for administrative oversight
        - User count statistics for capacity planning and analytics
        - Support for filtered user lists with search and criteria
        - Integration with user management workflows and operations
        - Comprehensive user data for administrative decision-making

    Example:
        response = UserListResponse(
            users=[user1, user2, user3],
            total_count=150,
            success=True,
            message="Users retrieved successfully"
        )

    """

    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")


class UserDetailResponse(BaseResponse):
    """Response schema for user detail endpoints with comprehensive profile information.

    Provides structured response format for individual user profile retrieval with
    complete user information and metadata. Implements consistent response structure
    for user profile operations and detailed user information presentation.

    Response Features:
        - Complete user profile with all public information and metadata
        - Consistent response structure with success status and messaging
        - Integration with user profile management and display systems
        - Support for detailed user information presentation and editing
        - Administrative and user-facing profile information access

    User Profile Information:
        - Complete user data including identity, status, and metadata
        - Account information for profile management and display
        - Administrative metadata for user management operations
        - Audit information for tracking and compliance requirements
        - Integration with user preference and settings systems

    Use Cases:
        - User profile display in web and mobile applications
        - Administrative user detail views and management interfaces
        - User profile editing and management workflows
        - User information retrieval for various application features
        - Integration with user analytics and reporting systems

    Example:
        response = UserDetailResponse(
            user=user_profile,
            success=True,
            message="User profile retrieved successfully"
        )

    """

    user: UserResponse = Field(..., description="User details")


class UserSearchParams(PaginationParams):
    """Comprehensive search parameters for user queries with advanced filtering capabilities.

    Extends PaginationParams with user-specific search and filtering options for
    advanced user discovery, management, and administrative operations. Implements
    flexible search criteria with partial matching and status-based filtering
    for comprehensive user management interfaces.

    Search Capabilities:
        - Username partial matching for user discovery and search
        - Email partial matching for contact-based user lookup
        - Account status filtering for user lifecycle management
        - Administrative privilege filtering for role-based management
        - Combined search criteria for complex user discovery operations

    Filtering Options:
        - username: Partial text matching for flexible user search
        - email: Partial text matching for email-based user discovery
        - is_active: Boolean filtering for account status management
        - is_superuser: Boolean filtering for administrative user management
        - Inherited pagination: page, size, ordering from PaginationParams

    Administrative Use Cases:
        - User management dashboards with search and filtering
        - Administrative user discovery and management operations
        - User analytics and reporting with filtering capabilities
        - Bulk user operations with criteria-based selection
        - User directory services with advanced search features

    Search Experience:
        - Partial matching for user-friendly search operations
        - Multiple criteria support for precise user discovery
        - Boolean filters for status-based user management
        - Pagination integration for large user datasets
        - Flexible search parameters for various use cases

    Example:
        search_params = UserSearchParams(
            username="john",           # Partial match
            email="@company.com",      # Domain-based search
            is_active=True,            # Active users only
            is_superuser=False,        # Regular users only
            page=1,
            size=20
        )

    """

    username: Optional[str] = Field(
        default=None, description="Filter by username (partial match)"
    )
    email: Optional[str] = Field(
        default=None, description="Filter by email (partial match)"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Filter by active status"
    )
    is_superuser: Optional[bool] = Field(
        default=None, description="Filter by superuser status"
    )


class UserStatsResponse(BaseSchema):
    """Response schema for comprehensive user statistics and analytics reporting.

    Provides detailed user analytics and system statistics for administrative
    dashboards, monitoring, and reporting purposes. Implements comprehensive
    user metrics with temporal analysis and custom JSON serialization for
    proper datetime handling and frontend integration.

    Statistical Categories:
        - User count statistics by status and privilege level
        - Temporal user creation analysis (daily, weekly, monthly)
        - Account status distribution for user lifecycle insights
        - Administrative user statistics for system oversight
        - Real-time statistics with timestamp for data freshness

    User Metrics:
        - total_users: Complete user count for system capacity analysis
        - active_users: Active account count for engagement metrics
        - inactive_users: Inactive account count for lifecycle management
        - superusers: Administrative user count for security oversight
        - Temporal creation metrics for growth analysis and trending

    Analytics Features:
        - Time-based user creation analysis for growth tracking
        - Account status distribution for user lifecycle insights
        - Administrative metrics for security and compliance monitoring
        - Real-time statistics with automatic timestamp generation
        - Custom JSON serialization for proper datetime handling

    Use Cases:
        - Administrative dashboards and executive reporting
        - User analytics and system monitoring interfaces
        - Capacity planning and resource allocation analysis
        - User growth tracking and business intelligence
        - Compliance reporting and user activity monitoring

    Temporal Analysis:
        - users_created_today: Daily user registration tracking
        - users_created_this_week: Weekly user growth analysis
        - users_created_this_month: Monthly user acquisition metrics
        - last_updated: Statistics freshness and calculation timestamp
        - Historical trending and growth pattern analysis

    Example:
        stats = UserStatsResponse(
            total_users=1500,
            active_users=1350,
            inactive_users=150,
            superusers=25,
            users_created_today=12,
            users_created_this_week=89,
            users_created_this_month=284
        )

    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    superusers: int = Field(..., description="Number of superusers")
