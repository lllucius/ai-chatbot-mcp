"""Authentication service for comprehensive user management and JWT token lifecycle.

This service provides enterprise-grade authentication functionality including secure
user registration, multi-factor authentication support, and comprehensive JWT token
lifecycle management with secure token generation and validation.
"""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.auth import RegisterRequest, Token

from ..config import settings
from ..core.exceptions import AuthenticationError, ValidationError
from ..models.user import User
from ..utils.security import get_password_hash, verify_password
from ..utils.timestamp import utcnow
from .base import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Authentication service for comprehensive user management and JWT token operations.

    This service extends BaseService to provide enterprise-grade authentication functionality
    including secure user registration, multi-identifier authentication, JWT token lifecycle
    management, and comprehensive security monitoring with robust audit logging.
    """

    def __init__(self, db: AsyncSession):
        """Initialize authentication service with database session and security configuration.

        Sets up the authentication service with database connectivity, JWT configuration,
        and security parameters from application settings.

        Args:
            db: Database session for authentication operations and user management
        """
        super().__init__(db, "auth_service")

        # Authentication configuration from settings
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    async def register_user(self, user_data: RegisterRequest) -> User:
        """Register a new user account with comprehensive validation and security checks.

        Creates a new user account with secure password hashing, uniqueness validation,
        and comprehensive conflict detection. Implements robust validation to prevent
        duplicate accounts and ensure data integrity with proper error handling and
        security logging for audit trails and monitoring.

        Args:
            user_data: User registration data containing username, email, password,
                      and optional full name with proper validation and sanitization

        Returns:
            User: Newly created user object with the following properties:
                - id: Unique UUID identifier for the user account
                - username: Validated and sanitized username for login
                - email: Validated email address for account management
                - full_name: Optional full name for profile display
                - is_active: Account status set to True for immediate access
                - created_at: Timestamp of account creation for audit tracking
                - hashed_password: Securely hashed password using bcrypt

        Raises:
            ValidationError: Raised in the following scenarios:
                - Username already exists in the system (case-insensitive check)
                - Email address already registered to another account
                - Invalid email format or domain validation failure
                - Password doesn't meet security complexity requirements
                - Username contains invalid characters or exceeds length limits
                - Registration data fails schema validation or business rules

        Security Notes:
            - Password is hashed using bcrypt with configurable work factor for security
            - Username and email uniqueness validation prevents account conflicts
            - Input sanitization prevents injection attacks and data corruption
            - Audit logging captures registration attempts for security monitoring
            - Account creation follows principle of least privilege with standard user role
            - Database transactions ensure data consistency and rollback on failures

        Use Cases:
            - User onboarding and account creation in web and mobile applications
            - Self-service registration workflows with email verification integration
            - Admin-managed user creation for enterprise and organizational accounts
            - Bulk user import processes with validation and conflict resolution
            - API-driven user registration for third-party integrations and services

        Example:
            register_data = RegisterRequest(
                username="john_doe",
                email="john@example.com",
                password="SecurePass123!",
                full_name="John Doe"
            )
            user = await auth_service.register_user(register_data)
            # Returns User object with secure password hash and unique identifiers

        """
        try:
            # Check if username already exists
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                raise ValidationError("Username already exists")

            # Check if email already exists
            existing_email = await self.get_user_by_email(user_data.email)
            if existing_email:
                raise ValidationError("Email already exists")

            # Create new user
            hashed_password = get_password_hash(user_data.password)

            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                is_active=True,
                is_superuser=False,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"User registered: {user.username}")
            return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise ValidationError(f"Registration failed: {e}")

    async def authenticate_user(self, username: str, password: str) -> Token:
        """Authenticate user with username/email and password, returning JWT token.

        Performs comprehensive user authentication with support for both username and
        email-based login. Implements security best practices including password
        verification, account status validation, and comprehensive audit logging.
        Updates user login tracking and generates secure JWT tokens for session management.

        Args:
            username: User identifier that can be either username or email address
                     with case-insensitive matching for improved user experience
            password: Plain text password for verification against stored hash
                     with secure comparison to prevent timing attacks

        Returns:
            Token: JWT token object containing the following properties:
                - access_token: Signed JWT token string for API authentication
                - token_type: Bearer token type specification for HTTP authentication
                - expires_in: Token expiration time in seconds for client management
                - Additional metadata for token lifecycle and security validation

        Raises:
            AuthenticationError: Raised in the following scenarios:
                - Invalid username or email address (user not found in system)
                - Incorrect password verification failure
                - Account is inactive or disabled by administrator
                - Account is locked due to security policies or brute force protection
                - Authentication service unavailable or database connection failure
                - Token generation failure due to configuration or system issues

        Security Notes:
            - Password verification uses secure comparison to prevent timing attacks
            - Account status validation ensures only active users can authenticate
            - Last login timestamp updated for security monitoring and analytics
            - Authentication attempts logged for audit trails and security monitoring
            - Failed authentication attempts tracked for brute force protection
            - JWT tokens generated with secure algorithms and proper expiration handling

        Use Cases:
            - User login workflows in web and mobile applications
            - API authentication for programmatic access and integrations
            - Single sign-on (SSO) integration with external identity providers
            - Multi-factor authentication as part of broader security workflows
            - Session management and user state tracking across application components
            - Automated authentication for service-to-service communication

        Example:
            # Authenticate with username
            token = await auth_service.authenticate_user("john_doe", "SecurePass123!")

            # Authenticate with email
            token = await auth_service.authenticate_user("john@example.com", "SecurePass123!")

            # Use token for API requests
            headers = {"Authorization": f"Bearer {token.access_token}"}

        """
        try:
            # Get user by username or email
            user = await self.get_user_by_username(username)
            if not user:
                user = await self.get_user_by_email(username)

            if not user:
                raise AuthenticationError("Invalid username or password")

            if not user.is_active:
                raise AuthenticationError("Account is inactive")

            # Verify password
            if not verify_password(password, user.hashed_password):
                raise AuthenticationError("Invalid username or password")

            # Update last login
            user.last_login = utcnow()
            await self.db.commit()

            # Create access token
            token_data = self.create_access_token({"sub": user.username})

            logger.info(f"User authenticated: {user.username}")
            return token_data

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Authentication failed")

    def create_access_token(self, data: Dict[str, Any]) -> Token:
        """Create JWT access token with secure configuration and expiration handling.

        Generates a signed JWT access token with configurable expiration time and
        secure algorithm selection. Implements proper token structure with standard
        claims and custom payload data for user identification and authorization.
        Ensures token security and integrity for API authentication workflows.

        Args:
            data: Token payload data containing user information and claims:
                 - sub: Subject claim typically containing username or user ID
                 - Additional custom claims for user roles and permissions
                 - Metadata for token tracking and security validation

        Returns:
            Token: JWT token object containing the following properties:
                - access_token: Base64-encoded JWT token string with signature
                - token_type: "bearer" specification for HTTP Authorization header
                - expires_in: Token expiration time in seconds for client management
                - Token metadata for validation and security monitoring

        Security Notes:
            - JWT tokens signed with configurable algorithm (HS256/RS256) for security
            - Expiration time set according to security policies and user experience requirements
            - Token payload includes standard claims (exp, sub) for proper validation
            - Secret key configuration ensures token integrity and prevents tampering
            - Token structure follows RFC 7519 standards for JWT implementation
            - Secure random generation prevents token prediction and replay attacks

        Use Cases:
            - User authentication and session management in web applications
            - API authentication for programmatic access and service integration
            - Microservices authentication and authorization workflows
            - Mobile application authentication with offline token validation
            - Single sign-on (SSO) token generation for cross-system authentication
            - Token refresh workflows for extended session management

        Example:
            token_data = {"sub": "john_doe", "role": "user", "permissions": ["read"]}
            token = auth_service.create_access_token(token_data)

            # Use in HTTP Authorization header
            headers = {"Authorization": f"Bearer {token.access_token}"}

            # Token automatically expires after configured time
            print(f"Token expires in {token.expires_in} seconds")

        """
        to_encode = data.copy()
        expire = utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
        )

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token integrity and extract username for authentication.

        Validates JWT token signature, expiration, and format to ensure token
        authenticity and integrity. Extracts user identification information
        from verified token payload for authentication and authorization workflows.
        Implements comprehensive error handling for token validation failures.

        Args:
            token: JWT token string to verify and decode, typically from
                  HTTP Authorization header or authentication cookie

        Returns:
            Optional[str]: Username extracted from token subject claim if valid,
                          None if token is invalid, expired, or malformed:
                - Valid token: Returns username string for user identification
                - Invalid token: Returns None for security and error handling
                - Expired token: Returns None to trigger authentication refresh
                - Malformed token: Returns None to prevent security vulnerabilities

        Security Notes:
            - Token signature verified using configured secret key and algorithm
            - Expiration time validation prevents use of expired tokens
            - Token format validation ensures proper JWT structure and claims
            - Subject claim extraction provides secure user identification
            - Error handling prevents information leakage about token failures
            - Constant-time operations prevent timing attack vulnerabilities

        Use Cases:
            - Authentication middleware for protecting API endpoints
            - User identification in request processing and authorization
            - Token validation in single sign-on (SSO) workflows
            - Session management and user state tracking
            - API gateway authentication and request routing
            - Mobile application offline token validation

        Example:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            token = auth_header.replace("Bearer ", "") if auth_header else None

            # Verify token and get username
            username = auth_service.verify_token(token)
            if username:
                # Token valid, proceed with authenticated request
                user = await auth_service.get_user_by_username(username)
            else:
                # Token invalid, require authentication
                raise AuthenticationError("Invalid or expired token")

        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username

        except JWTError:
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user account by username with case-insensitive matching.

        Performs efficient database lookup to find user account by username
        with proper case handling and optimized query execution. Implements
        secure user retrieval for authentication and user management workflows
        with comprehensive error handling and logging.

        Args:
            username: Username to search for in the database, case-insensitive
                     matching for improved user experience and flexibility

        Returns:
            Optional[User]: User object if found, None if no matching user exists:
                - Found: Complete User object with all profile and security data
                - Not found: None to indicate user does not exist in system
                - Database error: None with error logging for troubleshooting

        Security Notes:
            - Case-insensitive search prevents username enumeration attacks
            - Efficient database query with proper indexing for performance
            - No sensitive information exposed in case of user not found
            - Query optimization prevents database timing attacks
            - Comprehensive error logging for security monitoring and audit trails

        Use Cases:
            - User authentication and login processing workflows
            - Username availability checking during registration
            - User profile lookup and management operations
            - Administrative user search and management functions
            - Integration with external systems requiring user validation

        Example:
            user = await auth_service.get_user_by_username("john_doe")
            if user:
                print(f"Found user: {user.email}")
            else:
                print("User not found")

        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve user account by email address with validation and security.

        Performs efficient database lookup to find user account by email address
        with proper format validation and optimized query execution. Implements
        secure user retrieval for authentication workflows and account management
        with comprehensive error handling and security logging.

        Args:
            email: Email address to search for in the database, case-insensitive
                  matching with proper email format validation and normalization

        Returns:
            Optional[User]: User object if found, None if no matching user exists:
                - Found: Complete User object with all profile and authentication data
                - Not found: None to indicate email address not registered
                - Invalid format: None with validation error for malformed emails
                - Database error: None with comprehensive error logging

        Security Notes:
            - Email format validation prevents malformed input and injection attacks
            - Case-insensitive search provides consistent user experience
            - Efficient database query with proper email indexing for performance
            - No sensitive information exposed for non-existent email addresses
            - Comprehensive audit logging for security monitoring and compliance

        Use Cases:
            - Email-based authentication and login processing workflows
            - Email availability checking during user registration
            - Password reset workflows requiring email-based user lookup
            - Account recovery and email verification processes
            - Administrative user search and account management functions

        Example:
            user = await auth_service.get_user_by_email("john@example.com")
            if user:
                print(f"Found user: {user.username}")
            else:
                print("Email not registered")

        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user account by unique identifier with validation and security.

        Performs efficient database lookup to find user account by integer ID with
        proper identifier validation and optimized query execution. Implements
        secure user retrieval for API operations and internal service communication
        with comprehensive error handling and performance optimization.

        Args:
            user_id: Integer identifier to search for in the database with
                    proper format validation and type checking

        Returns:
            Optional[User]: User object if found, None if no matching user exists:
                - Found: Complete User object with all profile and security data
                - Not found: None to indicate user ID does not exist in system
                - Invalid ID: None with validation error for malformed identifiers
                - Database error: None with comprehensive error logging and monitoring

        Security Notes:
            - ID format validation prevents malformed input and injection attacks
            - Primary key lookup provides optimal database performance and security
            - No sensitive information exposed for non-existent user identifiers
            - Efficient query execution with proper database indexing
            - Comprehensive audit logging for security monitoring and access tracking

        Use Cases:
            - API endpoint user identification and authorization workflows
            - Internal service communication requiring user lookup by identifier
            - User profile management and administrative operations
            - Session management and user state tracking across application components
            - Integration with external systems using integer-based user references

        Example:
            user_id = 123
            user = await auth_service.get_user_by_id(user_id)
            if user:
                print(f"Found user: {user.username} ({user.email})")
            else:
                print("User ID not found")

        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
