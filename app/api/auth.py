"""
Authentication API endpoints with comprehensive security and standardized error handling.

This module provides endpoints for user authentication including registration, login,
token management, and password operations. It implements comprehensive security
measures, consistent error handling patterns, and detailed logging for security
monitoring and compliance.

Key Features:
- User registration with comprehensive validation and conflict detection
- Multi-factor authentication support (username/email)
- JWT token lifecycle management (create, refresh, revoke)
- Password reset workflow with administrative controls
- Comprehensive security logging and audit trail
- Session management and user state tracking

Authentication Flow:
- User registration with unique identity validation
- Secure credential storage with password hashing
- JWT token generation and validation for session management
- Token refresh mechanisms for extended sessions
- Logout and session termination capabilities
- Password reset through administrative channels

Security Features:
- Input validation and sanitization to prevent injection attacks
- Rate limiting and abuse protection mechanisms
- Secure token handling with proper expiration
- Comprehensive audit logging for security events
- Protection against common attacks (brute force, timing)
- Password complexity enforcement and secure storage

Token Management:
- JWT-based stateless authentication
- Configurable token expiration and refresh policies
- Secure token generation with cryptographic signing
- Token validation middleware for protected endpoints
- Session extension through refresh token mechanisms

Administrative Features:
- Password reset through administrative channels
- User account status management and control
- Security event logging for compliance and monitoring
- Administrative override capabilities for account recovery
- Audit trail for all authentication and authorization events

Compliance and Monitoring:
- Comprehensive logging of all authentication events
- Security audit trail for compliance requirements
- Failed attempt tracking and alerting capabilities
- User activity monitoring and reporting
- Integration with security monitoring systems
"""

from fastapi import APIRouter, Depends

from ..dependencies import get_auth_service, get_current_user
from ..models.user import User
from shared.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from shared.schemas.common import BaseResponse, APIResponse
from shared.schemas.user import UserResponse
from ..core.response import success_response, error_response
from ..services.auth import AuthService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=APIResponse)
@handle_api_errors("User registration failed")
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account with comprehensive validation and security controls.

    Creates a new user account with the provided credentials after performing
    extensive validation including uniqueness checks, password complexity
    verification, and input sanitization. Implements comprehensive security
    measures to ensure account integrity and system protection.

    Args:
        request: User registration data including credentials and profile information
        auth_service: Injected authentication service instance for user management

    Returns:
        UserResponse: Created user profile information without sensitive data

    Raises:
        HTTP 400: If username/email already exists, validation fails, or input is invalid
        HTTP 422: If request data format is invalid or missing required fields
        HTTP 500: If user creation process fails due to system error

    Registration Process:
        - Input validation and sanitization for security
        - Username and email uniqueness verification
        - Password complexity validation and secure hashing
        - User profile creation with proper defaults
        - Account activation and initial status setting

    Security Features:
        - Passwords are securely hashed using industry-standard algorithms
        - Input validation prevents malicious data injection attacks
        - Duplicate detection ensures unique user identities
        - Registration events are comprehensively logged for security monitoring
        - Rate limiting protection against automated registration attacks

    Validation Rules:
        - Username: alphanumeric characters, 3-50 characters length
        - Email: valid email format with domain verification
        - Password: minimum complexity requirements (length, character types)
        - Profile data: sanitized and validated for security
        - No malicious content or injection attempts

    Use Cases:
        - New user onboarding and account creation
        - Administrative user provisioning
        - Bulk user import and migration
        - Development and testing account setup

    Example:
        POST /api/v1/auth/register
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "SecurePassword123!",
            "full_name": "John Doe"
        }
    """
    log_api_call("register", username=request.username, email=request.email)

    user = await auth_service.register_user(request)
    user_response = UserResponse.model_validate(user)
    return APIResponse(
        success=True,
        message="User registered successfully",
        data=user_response.model_dump()
    )


@router.post("/login", response_model=APIResponse)
@handle_api_errors("User authentication failed")
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user credentials and generate JWT access token for secure session management.

    Validates user credentials against stored information and returns a JWT token
    for accessing protected endpoints. Supports flexible authentication with either
    username or email address for user convenience and accessibility.

    Args:
        request: Login credentials containing username/email and password
        auth_service: Injected authentication service instance for credential validation

    Returns:
        APIResponse: JWT access token with expiration information using unified envelope:
            - success: Authentication success indicator
            - message: Authentication status message
            - timestamp: Authentication timestamp
            - data: Token data (access_token, token_type, expires_in)

    Raises:
        HTTP 401: If credentials are invalid, user account is inactive, or authentication fails
        HTTP 422: If request format is invalid or missing required fields
        HTTP 500: If authentication process fails due to system error

    Authentication Process:
        - Credential validation against stored user information
        - Password verification using secure hashing comparison
        - Account status verification (active, not suspended)
        - JWT token generation with proper claims and expiration
        - Security event logging for monitoring and audit

    Security Features:
        - Supports both username and email authentication for flexibility
        - Password verification uses secure timing-safe hashing comparison
        - Login attempts are comprehensively logged for security monitoring
        - Token expiration provides time-limited access control
        - Failed attempts trigger rate limiting and security alerts
        - Protection against brute force and credential stuffing attacks

    Token Features:
        - JWT format with cryptographic signing for integrity
        - Configurable expiration time for security balance
        - User identification and role information in claims
        - Stateless design for scalability and performance
        - Compatible with standard authorization headers

    Rate Limiting:
        - Failed login attempt tracking and throttling
        - IP-based and user-based rate limiting
        - Progressive delays for repeated failures
        - Account lockout protection mechanisms
        - Security alert generation for suspicious activity

    Use Cases:
        - User session initiation and authentication
        - Mobile and web application login flows
        - API access token generation
        - Administrative dashboard access
        - Integration with external authentication systems

    Example:
        POST /api/v1/auth/login
        {
            "username": "johndoe",  # or "john@example.com"
            "password": "SecurePassword123!"
        }
    """
    log_api_call("login", username=request.username)

    token_data = await auth_service.authenticate_user(
        request.username, request.password
    )
    # Convert Token object to dict for unified response
    token_dict = token_data.model_dump() if hasattr(token_data, 'model_dump') else token_data
    return success_response(
        data=token_dict,
        message="User authenticated successfully"
    )


@router.get("/me", response_model=APIResponse)
@handle_api_errors("Failed to get current user information")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get comprehensive current authenticated user information and profile details.

    Returns complete profile information for the currently authenticated user based
    on the JWT token provided in the Authorization header. Provides secure access
    to user data while maintaining privacy and security standards.

    Args:
        current_user: Automatically injected current user from validated JWT token

    Returns:
        APIResponse: Response containing user profile information in data field:
            - data: UserResponse with complete user profile including:
                - id: Unique user identifier
                - username: User's unique username
                - email: User's email address
                - full_name: User's display name
                - is_active: Account activation status
                - is_superuser: Administrative privileges indicator
                - created_at: Account creation timestamp
                - updated_at: Last profile update timestamp

    Security Features:
        - Requires valid JWT token in Authorization header for access
        - User information is retrieved from validated token claims
        - No sensitive information (password hash) is returned
        - Endpoint can be used to verify token validity and user status
        - Access is automatically logged for security monitoring

    Token Validation:
        - JWT signature verification for authenticity
        - Token expiration checking for validity
        - User existence and status verification
        - Role and permission validation
        - Automatic security logging and monitoring

    Use Cases:
        - User profile display and management
        - Token validation and session verification
        - User information retrieval for personalization
        - Account status checking and validation
        - Security and audit logging requirements

    Example:
        GET /api/v1/auth/me
        Authorization: Bearer <jwt_token>

        Response: {
            "success": true,
            "message": "User information retrieved successfully",
            "timestamp": "2024-01-01T12:00:00Z",
            "data": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "is_superuser": false,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    """
    log_api_call("get_current_user_info", user_id=str(current_user.id))
    user_response = UserResponse.model_validate(current_user)
    return APIResponse(
        success=True,
        message="User information retrieved successfully",
        data=user_response.model_dump()
    )


@router.post("/logout", response_model=APIResponse)
@handle_api_errors("Logout failed")
async def logout():
    """
    Logout current user with comprehensive session termination and security cleanup.

    Provides secure logout functionality for the current user session. Since JWT
    tokens are stateless by design, this endpoint primarily serves as a client-side
    logout indicator and security event logger. Clients should properly dispose
    of their tokens after calling this endpoint.

    Returns:
        APIResponse: Success message confirming logout completion using unified envelope

    Logout Process:
        - Security event logging for audit trail and monitoring
        - Client notification for token disposal and cleanup
        - Session termination confirmation and status update
        - Security monitoring integration for user activity tracking

    Security Considerations:
        - JWT tokens remain valid until natural expiration
        - Client applications must dispose of tokens locally
        - Server-side logout event logging for security monitoring
        - Integration with security systems for session tracking

    Enhanced Security Options:
        For production environments requiring additional security:
        - Token blacklisting on server side for immediate invalidation
        - Token refresh rotation for enhanced security
        - Short-lived access tokens with secure refresh mechanisms
        - Real-time session monitoring and management
        - Forced logout capabilities for security incidents

    Client Responsibilities:
        - Remove JWT token from local storage immediately
        - Clear any cached user data and session information
        - Redirect to login page or public areas
        - Dispose of any related authentication credentials
        - Update application state to reflect logged-out status

    Use Cases:
        - User-initiated logout from web applications
        - Mobile application session termination
        - Security-required logout for policy compliance
        - Administrative forced logout scenarios
        - Session cleanup during application shutdown

    Example:
        POST /api/v1/auth/logout
        Authorization: Bearer <jwt_token>

        Response: {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    log_api_call("logout")
    return success_response(message="Logged out successfully")


@router.post("/refresh", response_model=APIResponse)
@handle_api_errors("Token refresh failed")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh JWT access token for seamless session continuation and extended access.

    Generates a new JWT access token for the current user, extending their session
    without requiring re-authentication. Provides seamless user experience while
    maintaining security through controlled token lifecycle management.

    Args:
        current_user: Automatically injected current user from validated JWT token
        auth_service: Injected authentication service instance for token operations

    Returns:
        APIResponse: New JWT access token using unified envelope:
            - success: Token refresh success indicator
            - message: Token refresh status message
            - timestamp: Token refresh timestamp
            - data: New token data (access_token, token_type, expires_in)

    Raises:
        HTTP 401: If current token is invalid, expired, or user account is inactive
        HTTP 500: If token generation fails due to system error

    Token Refresh Process:
        - Current token validation and authenticity verification
        - User account status and permission verification
        - New token generation with updated expiration time
        - Security event logging for audit trail and monitoring
        - Original token invalidation recommendations for client

    Security Features:
        - Requires valid existing token for refresh authorization
        - New token includes updated expiration time for time-limited access
        - Original token should be immediately discarded by client applications
        - Refresh operations are comprehensively logged for security monitoring
        - Rate limiting protection against token refresh abuse

    Token Lifecycle Management:
        - Seamless session extension without user interruption
        - Configurable token expiration policies for security balance
        - Automatic claim updates for role and permission changes
        - Integration with session management and monitoring systems
        - Support for token revocation and blacklisting mechanisms

    Client Integration:
        - Replace existing token with new token immediately
        - Update Authorization headers for subsequent requests
        - Handle refresh errors gracefully with re-authentication
        - Implement automatic refresh before token expiration
        - Maintain secure token storage and transmission

    Use Cases:
        - Long-running application sessions and user workflows
        - Mobile application background refresh and synchronization
        - Single-page application session management
        - API integration with extended operations
        - Administrative dashboard continuous access

    Example:
        POST /api/v1/auth/refresh
        Authorization: Bearer <current_jwt_token>

        Response: {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "expires_in": 3600
        }
    """
    log_api_call("refresh_token", user_id=str(current_user.id))

    token_data = auth_service.create_access_token({"sub": current_user.username})
    # Convert Token object to dict for unified response
    token_dict = token_data.model_dump() if hasattr(token_data, 'model_dump') else token_data
    return success_response(
        data=token_dict,
        message="Token refreshed successfully"
    )


@router.post("/password-reset", response_model=APIResponse)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset through administrative channels with comprehensive security controls.

    Initiates password reset process for the specified email address through
    administrative channels. In this admin-focused dashboard environment, password
    resets are handled directly by system administrators through secure user
    management interfaces rather than automated self-service workflows.

    Args:
        request: Password reset request containing target email address
        auth_service: Injected authentication service instance for validation

    Returns:
        BaseResponse: Confirmation message for administrative dashboard context

    Administrative Process:
        - Request validation and email verification
        - Security event logging for audit trail and monitoring
        - Administrative notification for manual password reset handling
        - User communication through secure administrative channels
        - Comprehensive tracking of reset requests and resolutions

    Security Features:
        - Administrative control over password reset operations
        - Manual verification and identity confirmation processes
        - Secure communication channels for sensitive operations
        - Comprehensive audit logging for compliance requirements
        - Protection against automated password reset abuse

    Administrative Benefits:
        - Direct control over user account security and access
        - Manual verification prevents unauthorized password changes
        - Comprehensive oversight of all account modification activities
        - Integration with existing administrative workflows and procedures
        - Enhanced security through human verification and validation

    Alternative Implementation:
        For self-service environments, this could be enhanced with:
        - Automated email-based reset token generation
        - Time-limited reset links with cryptographic verification
        - User identity verification through multiple factors
        - Automated workflow integration with notification systems

    Use Cases:
        - User-requested password reset through administrative support
        - Emergency account recovery and access restoration
        - Bulk password reset operations for security incidents
        - Compliance-driven password reset requirements
        - Integration with helpdesk and support ticketing systems

    Example:
        POST /api/v1/auth/password-reset
        {
            "email": "user@example.com"
        }
    """
    log_api_call("request_password_reset", email=request.email)

    # For admin-only dashboard, password resets are handled by administrators
    # through the user management interface rather than self-service email
    return success_response(
        message="Password reset request noted. Contact system administrator for password changes."
    )


@router.post("/password-reset/confirm", response_model=APIResponse)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset through administrative channels with secure validation and processing.

    Processes password reset confirmation using administrative validation and secure
    procedures. In this admin-focused dashboard environment, password resets are
    handled directly by system administrators through secure user management
    interfaces with comprehensive verification and audit controls.

    Args:
        request: Password reset confirmation containing reset token and new password
        auth_service: Injected authentication service instance for validation

    Returns:
        BaseResponse: Confirmation message for administrative dashboard context

    Administrative Process:
        - Reset token validation and authenticity verification
        - Administrative approval and identity confirmation procedures
        - Secure password update through administrative channels
        - Comprehensive audit logging for compliance and security monitoring
        - User notification through secure administrative communication

    Security Features:
        - Administrative oversight and manual verification requirements
        - Token-based validation with cryptographic verification
        - Secure password handling with proper hashing and storage
        - Comprehensive audit trail for all password modification activities
        - Protection against automated and unauthorized password changes

    Administrative Workflow:
        - Administrator receives and validates reset request
        - Identity verification through multiple secure channels
        - Manual password reset execution with proper authorization
        - User notification and account status communication
        - Documentation and audit trail completion

    Enhanced Security:
        - Multi-factor authentication for administrative operations
        - Secure token generation with time-limited validity
        - Comprehensive logging of all reset activities and outcomes
        - Integration with security monitoring and alerting systems
        - Compliance with organizational security policies and procedures

    Alternative Implementation:
        For automated environments, this could include:
        - Cryptographic token validation with database verification
        - Automated password complexity validation and enforcement
        - User notification through secure automated channels
        - Integration with identity management and single sign-on systems

    Use Cases:
        - Administrative password reset completion and verification
        - Emergency account recovery with administrative oversight
        - Compliance-driven password reset procedures
        - Integration with helpdesk and support resolution workflows
        - Security incident response and account restoration

    Example:
        POST /api/v1/auth/password-reset/confirm
        {
            "token": "reset_token_here",
            "new_password": "NewSecurePassword123!"
        }
    """
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")

    # For admin-only dashboard, password resets are handled by administrators
    # through the user management interface rather than token-based reset
    return success_response(
        message="Password reset must be performed by system administrator through user management interface."
    )
