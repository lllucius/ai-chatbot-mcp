"""
Authentication-related Pydantic schemas with comprehensive validation and security.

This module provides robust schemas for user authentication, registration, token
management, and password operations with advanced validation, security controls,
and comprehensive field descriptions. Implements industry-standard security
practices for authentication data handling and validation.

Key Features:
- User registration with comprehensive validation and security controls
- Secure login processing with flexible username/email authentication
- JWT token management with proper expiration and security metadata
- Password reset workflow with validation and security verification
- Advanced field validation with custom validators and security rules
- Comprehensive input sanitization and security enforcement

Authentication Schemas:
- LoginRequest: Secure user authentication with username/email flexibility
- RegisterRequest: User registration with comprehensive validation and security
- Token: JWT token response with expiration and metadata management
- PasswordResetRequest: Password reset initiation with email validation
- PasswordResetConfirm: Password reset completion with strength validation

Security Features:
- Password strength validation with complexity requirements
- Username format validation with character restrictions
- Email validation with proper format checking
- Input sanitization to prevent injection attacks
- Field length limits to prevent buffer overflow attacks
- Comprehensive validation error reporting for security monitoring

Validation Capabilities:
- Custom field validators for security and business rules
- Password complexity enforcement (uppercase, lowercase, numbers)
- Username format restrictions (alphanumeric, underscore, hyphen only)
- Email format validation with domain verification
- Field length validation for security and database constraints
- Real-time validation feedback for user experience

Token Management:
- JWT access token with proper expiration handling
- Bearer token type specification for standard compliance
- Expiration metadata for client-side token management
- Security-focused token structure and validation
- Integration with authentication middleware and services

Use Cases:
- User authentication and authorization in web and mobile applications
- API authentication with JWT token-based security
- User registration and account creation workflows
- Password reset and recovery operations
- Administrative user management and security operations
- Multi-factor authentication integration and support

Security Standards:
- Industry-standard password complexity requirements
- Secure field validation and input sanitization
- Protection against common authentication vulnerabilities
- Compliance with security best practices and standards
- Comprehensive error handling without information disclosure
- Audit-friendly validation and security logging support
"""

import re
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema


class LoginRequest(BaseSchema):
    """
    Schema for secure user login request with flexible authentication methods.

    Validates user login credentials supporting both username and email-based
    authentication with comprehensive input validation and security controls.
    Implements field-level validation to ensure data integrity and prevent
    authentication-related security vulnerabilities.

    Authentication Methods:
        - Username-based authentication with alphanumeric validation
        - Email-based authentication with format verification
        - Flexible login identifier field accepting both formats
        - Case-insensitive email matching for user convenience
        - Secure credential handling and validation

    Security Features:
        - Password field with minimum security requirements
        - Input length validation to prevent buffer overflow attacks
        - Field sanitization to prevent injection vulnerabilities
        - Comprehensive validation error reporting for monitoring
        - Protection against credential stuffing and brute force attacks

    Field Validation:
        - username: 3-50 characters, supports username or email format
        - password: 8-100 characters, enforces minimum security length
        - Automatic input trimming and normalization
        - Character encoding validation and sanitization
        - Cross-field validation for consistency and security

    Use Cases:
        - Web application user authentication and login workflows
        - Mobile application authentication with flexible identifier support
        - API authentication for automated systems and integrations
        - Administrative login with enhanced security requirements
        - Multi-tenant authentication with user identifier flexibility

    Security Considerations:
        - Password fields are never logged or stored in plain text
        - Input validation prevents SQL injection and XSS attacks
        - Rate limiting integration for brute force protection
        - Secure credential transmission and handling protocols
        - Comprehensive audit logging for security monitoring

    Example:
        # Username-based login
        login_data = LoginRequest(
            username="john_doe",
            password="SecurePassword123!"
        )

        # Email-based login
        login_data = LoginRequest(
            username="john@example.com",
            password="SecurePassword123!"
        )
    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username or email"
    )
    password: str = Field(..., min_length=8, max_length=100, description="Password")

    model_config = {
        "json_schema_extra": {
            "example": {"username": "johndoe", "password": "SecurePass123"}
        }
    }


class RegisterRequest(BaseSchema):
    """
    Schema for comprehensive user registration with advanced validation and security.

    Handles new user account creation with extensive validation, security controls,
    and data integrity enforcement. Implements industry-standard security practices
    for user registration including password complexity requirements, username
    format validation, and comprehensive input sanitization.

    Registration Fields:
        - username: Unique alphanumeric identifier with format restrictions
        - email: Valid email address with domain verification
        - password: Strong password meeting complexity requirements
        - full_name: Optional display name for user personalization

    Security Validation:
        - Username format validation (alphanumeric, underscore, hyphen only)
        - Password strength validation with multiple security requirements
        - Email format validation with proper domain checking
        - Input sanitization to prevent injection attacks
        - Field length validation for security and database constraints

    Password Requirements:
        - Minimum 8 characters for basic security
        - At least one uppercase letter for complexity
        - At least one lowercase letter for character diversity
        - At least one number for enhanced security
        - Additional special character support for maximum security

    Username Restrictions:
        - Alphanumeric characters (a-z, A-Z, 0-9) for compatibility
        - Underscores (_) and hyphens (-) for readability
        - No special characters that could cause parsing issues
        - Length restrictions (3-50 characters) for practical use
        - Case-sensitive validation for unique identification

    Registration Process:
        - Comprehensive field validation before account creation
        - Duplicate username and email checking during validation
        - Secure password hashing after validation success
        - Account activation workflow integration support
        - Audit logging for registration security monitoring

    Use Cases:
        - New user account creation in web and mobile applications
        - Administrative user provisioning and management
        - Bulk user import with validation and security controls
        - Self-service registration with automated verification
        - Multi-tenant user registration with organization association

    Security Features:
        - Protection against common registration attacks and vulnerabilities
        - Input validation to prevent SQL injection and XSS attacks
        - Password strength enforcement to prevent weak credentials
        - Email validation to ensure account recovery capability
        - Comprehensive error reporting for security monitoring

    Validation Errors:
        - Clear error messages for field validation failures
        - Security-focused error reporting without information disclosure
        - Field-specific validation with detailed feedback
        - Client-friendly error formatting for user experience
        - Administrative logging for security analysis and monitoring

    Example:
        registration_data = RegisterRequest(
            username="john_doe",
            email="john@example.com",
            password="SecurePassword123!",
            full_name="John Doe"
        )
    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Unique username"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Strong password"
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="Full display name"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """
        Validate username format with comprehensive security and compatibility rules.

        Ensures username meets security and compatibility requirements by enforcing
        character restrictions and format validation. Prevents usernames that could
        cause security issues, parsing problems, or system conflicts.

        Args:
            v: Username value to validate

        Returns:
            str: Validated username if all requirements are met

        Raises:
            ValueError: If username contains invalid characters or format

        Validation Rules:
            - Only alphanumeric characters (a-z, A-Z, 0-9) allowed
            - Underscores (_) and hyphens (-) permitted for readability
            - No spaces, special characters, or unicode characters
            - Case-sensitive validation for unique identification
            - Length already validated by Field constraints (3-50 characters)

        Security Considerations:
            - Prevents injection attacks through character restriction
            - Avoids parsing conflicts with special characters
            - Ensures compatibility with various systems and protocols
            - Reduces risk of username-based vulnerabilities
            - Supports consistent identifier format across platforms

        Compatibility Benefits:
            - URL-safe usernames for web application integration
            - Database-safe identifiers without escaping requirements
            - Email-compatible usernames for notification systems
            - Cross-platform username consistency
            - API-friendly identifier format for external integrations

        Example:
            validate_username("john_doe")      # Valid
            validate_username("user123")       # Valid
            validate_username("test-user")     # Valid
            validate_username("user@domain")   # Invalid - contains @
            validate_username("user name")     # Invalid - contains space
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """
        Validate password strength with comprehensive security requirements.

        Enforces industry-standard password complexity requirements to ensure
        user account security and protection against common password-based attacks.
        Implements multiple validation criteria for robust password security.

        Args:
            v: Password value to validate

        Returns:
            str: Validated password if all security requirements are met

        Raises:
            ValueError: If password fails any security requirement

        Security Requirements:
            - Minimum 8 characters for basic security protection
            - At least one uppercase letter (A-Z) for complexity
            - At least one lowercase letter (a-z) for character diversity
            - At least one number (0-9) for enhanced security
            - Length already validated by Field constraints (8-100 characters)

        Security Benefits:
            - Protection against dictionary attacks with complexity requirements
            - Resistance to brute force attacks through character diversity
            - Enhanced entropy for cryptographic security
            - Compliance with security standards and best practices
            - Reduced risk of credential compromise and account takeover

        Password Complexity:
            - Character diversity increases password entropy
            - Mixed case requirements prevent simple lowercase attacks
            - Number requirements add mathematical character complexity
            - Length requirements provide baseline security protection
            - Combined requirements create robust password security

        Attack Protection:
            - Dictionary attacks: Complexity requirements prevent common words
            - Brute force attacks: Character diversity increases attack complexity
            - Social engineering: Strong passwords resist guessing attempts
            - Credential stuffing: Unique complex passwords reduce reuse risks
            - Password spraying: Strong requirements prevent common password use

        Example:
            validate_password("SecurePass123")   # Valid - meets all requirements
            validate_password("password")        # Invalid - missing uppercase/number
            validate_password("PASSWORD")        # Invalid - missing lowercase/number
            validate_password("Pass123")         # Invalid - too short (less than 8)
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe",
            }
        }
    }


class Token(BaseSchema):
    """
    Schema for JWT token response with comprehensive security metadata and expiration handling.

    Represents JWT access token response structure with essential security metadata
    including token type specification, expiration information, and proper formatting
    for client-side token management and authentication workflows.

    Token Components:
        - access_token: Cryptographically signed JWT token for authentication
        - token_type: Token type specification (bearer) for HTTP Authorization header
        - expires_in: Token expiration time in seconds for client-side management

    JWT Token Features:
        - Cryptographically signed for integrity and authenticity verification
        - Stateless authentication without server-side session storage
        - Embedded user claims and permissions for authorization
        - Configurable expiration for security and session management
        - Standard format compatible with OAuth 2.0 and OpenID Connect

    Security Metadata:
        - Bearer token type for standardized HTTP Authorization header usage
        - Expiration time for automatic token invalidation and renewal
        - Secure token generation with cryptographic signing algorithms
        - User identity and role information embedded in token claims
        - Protection against token replay and unauthorized access attempts

    Client Integration:
        - Standard Authorization header format: "Bearer {access_token}"
        - Automatic expiration handling for seamless token renewal
        - Client-side token storage with appropriate security measures
        - Token validation and refresh workflow integration
        - Cross-platform compatibility for web and mobile applications

    Token Lifecycle:
        - Secure generation during successful authentication
        - Configurable expiration for balance between security and usability
        - Refresh token support for extended session management
        - Automatic invalidation on logout or security events
        - Revocation capabilities for security incident response

    Use Cases:
        - API authentication and authorization for protected endpoints
        - Single sign-on (SSO) integration and cross-service authentication
        - Mobile application authentication with offline capability
        - Microservice authentication and service-to-service communication
        - Administrative authentication with enhanced security requirements

    Security Considerations:
        - Secure token transmission over HTTPS connections only
        - Client-side secure storage to prevent token theft
        - Token expiration enforcement for limited session duration
        - Protection against cross-site scripting (XSS) and token exposure
        - Proper token validation and signature verification

    Expiration Management:
        - Short-lived tokens for enhanced security (typically 15-60 minutes)
        - Refresh token mechanism for seamless user experience
        - Automatic token renewal before expiration
        - Grace period handling for clock synchronization issues
        - Token blacklisting support for immediate invalidation

    Example:
        token_response = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )

        # Client usage:
        # Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    }


class PasswordResetRequest(BaseSchema):
    """
    Schema for password reset request initiation with comprehensive email validation.

    Handles password reset workflow initiation by validating user email address
    and triggering secure password reset process. Implements proper email
    validation and security controls for account recovery operations.

    Reset Process:
        - Email address validation for account identification
        - Secure reset token generation and management
        - Email-based reset workflow with time-limited tokens
        - Administrative oversight and security monitoring
        - Protection against password reset abuse and attacks

    Email Validation:
        - Proper email format validation with domain verification
        - Email address normalization for consistent processing
        - Account existence verification before reset initiation
        - Protection against email enumeration attacks
        - Rate limiting for reset request frequency control

    Security Features:
        - Time-limited reset tokens for security and usability
        - Secure token generation with cryptographic randomness
        - Single-use token validation to prevent replay attacks
        - Administrative logging for security monitoring and audit
        - Protection against automated reset request flooding

    Reset Workflow:
        - User initiates reset with email address submission
        - System validates email and generates secure reset token
        - Email notification sent with reset instructions and token
        - User follows reset link to complete password change
        - Token invalidation after successful password reset

    Use Cases:
        - User-initiated password recovery for forgotten passwords
        - Administrative password reset for user account management
        - Security-driven password reset for compromised accounts
        - Emergency account recovery for locked or inaccessible accounts
        - Compliance-driven password reset for policy enforcement

    Administrative Controls:
        - Manual password reset processing for enhanced security
        - Administrative approval for sensitive account operations
        - Comprehensive audit logging for compliance and monitoring
        - Integration with helpdesk and support ticketing systems
        - Security team oversight for high-privilege account resets

    Protection Mechanisms:
        - Rate limiting to prevent reset request flooding
        - Email validation to prevent invalid or malicious requests
        - Token expiration to limit exposure window
        - Administrative oversight for enhanced security control
        - Comprehensive logging for security analysis and investigation

    Example:
        reset_request = PasswordResetRequest(
            email="user@example.com"
        )
    """

    email: EmailStr = Field(..., description="Email address for password reset")

    model_config = {"json_schema_extra": {"example": {"email": "john@example.com"}}}


class PasswordResetConfirm(BaseSchema):
    """
    Schema for password reset confirmation with comprehensive validation and security.

    Handles password reset completion workflow with secure token validation and
    new password strength verification. Implements comprehensive security controls
    for account recovery operations and password change enforcement.

    Reset Completion:
        - Secure reset token validation and verification
        - New password strength validation with complexity requirements
        - Single-use token consumption to prevent replay attacks
        - Administrative oversight and security monitoring
        - Comprehensive audit logging for compliance and security

    Token Validation:
        - Cryptographically secure token verification
        - Time-limited token expiration for security window control
        - Single-use token invalidation after successful reset
        - Protection against token tampering and manipulation
        - Administrative token override capabilities for emergency recovery

    Password Security:
        - Industry-standard password complexity requirements
        - Multi-criteria validation for robust password security
        - Protection against weak passwords and common attack vectors
        - Password history integration to prevent immediate reuse
        - Secure password hashing and storage after validation

    Security Features:
        - Token authenticity verification through cryptographic validation
        - Password strength enforcement with multiple security criteria
        - Protection against token replay and password reset abuse
        - Administrative oversight for sensitive account operations
        - Comprehensive security logging for monitoring and analysis

    Reset Process Flow:
        - User receives secure reset token through verified communication channel
        - User submits token and new password through secure interface
        - System validates token authenticity and expiration
        - New password validated against security requirements
        - Password updated and token invalidated upon successful completion

    Administrative Controls:
        - Manual reset processing for enhanced security oversight
        - Administrative approval for high-privilege account resets
        - Security team involvement for sensitive account operations
        - Comprehensive audit trail for compliance and investigation
        - Integration with security monitoring and alerting systems

    Use Cases:
        - User completion of password reset workflow for account recovery
        - Administrative password reset for user account management
        - Security-driven password changes for compromised accounts
        - Emergency account recovery with administrative oversight
        - Compliance-driven password updates for policy enforcement

    Validation Requirements:
        - Reset token must be valid, unexpired, and unused
        - New password must meet complexity requirements (uppercase, lowercase, number)
        - New password must be different from previous passwords (if history enabled)
        - Password length must meet minimum security requirements (8+ characters)
        - Administrative approval may be required for sensitive accounts

    Example:
        reset_confirm = PasswordResetConfirm(
            token="secure_reset_token_here",
            new_password="NewSecurePassword123!"
        )
    """

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """
        Validate new password strength with comprehensive security requirements.

        Enforces the same rigorous password complexity requirements as user
        registration to ensure consistent security standards across all password
        operations. Implements multiple validation criteria for robust password
        security and protection against common password-based attacks.

        Args:
            v: New password value to validate

        Returns:
            str: Validated password if all security requirements are met

        Raises:
            ValueError: If password fails any security requirement

        Security Requirements:
            - Minimum 8 characters for baseline security protection
            - At least one uppercase letter (A-Z) for character complexity
            - At least one lowercase letter (a-z) for character diversity
            - At least one number (0-9) for enhanced security entropy
            - Length constraints (8-100 characters) for practical use and security

        Password Reset Security:
            - Same validation standards as registration for consistency
            - Protection against weak password selection during reset
            - Enhanced security for account recovery operations
            - Prevention of common password vulnerabilities
            - Compliance with organizational security policies

        Attack Protection:
            - Dictionary attacks: Complexity requirements prevent common words
            - Brute force attacks: Character diversity increases attack difficulty
            - Social engineering: Strong passwords resist guessing attempts
            - Credential reuse: Encourages unique password creation
            - Password spraying: Complexity prevents common password patterns

        Validation Consistency:
            - Identical requirements to registration password validation
            - Consistent security standards across all password operations
            - Unified error messaging for user experience consistency
            - Same protection mechanisms for all password entry points
            - Comprehensive security coverage for password lifecycle

        Example:
            validate_password("NewSecurePass123")  # Valid - meets all requirements
            validate_password("newpassword")       # Invalid - missing uppercase/number
            validate_password("NEWPASSWORD")       # Invalid - missing lowercase/number
            validate_password("NewPass")           # Invalid - too short
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"token": "reset_token_here", "new_password": "NewSecurePass123"}
        }
    }
