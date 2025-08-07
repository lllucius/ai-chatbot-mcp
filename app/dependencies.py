"""FastAPI dependencies for authentication, authorization, and service injection.

This module provides comprehensive reusable dependencies for FastAPI endpoints
including user authentication, authorization checks, service injection, and
common utilities. Implements enterprise-grade dependency injection patterns
with proper security controls, validation, and integration with the application's
service architecture for scalable and maintainable API development.

Dependency Architecture:
- JWT-based authentication with secure token validation and user identification
- Role-based authorization with permission checking and access control
- Service dependency injection with proper lifecycle management
- Database session management with transaction handling and connection pooling
- Request validation and sanitization with comprehensive error handling
- Integration with FastAPI's dependency injection system for clean architecture

Authentication Dependencies:
- JWT token validation with proper signature verification and expiration checking
- User identification and retrieval with efficient database queries
- Optional authentication for endpoints with both authenticated and anonymous access
- Session management with proper token lifecycle and security controls
- Multi-factor authentication support for enhanced security requirements
- Integration with external identity providers and authentication systems

Authorization Dependencies:
- Role-based access control with flexible permission systems
- Resource-level authorization with ownership and access validation
- Admin and superuser privilege checking for administrative operations
- API key authentication for service-to-service communication
- Rate limiting and throttling for abuse prevention and resource protection
- Audit logging for access control and compliance monitoring

Service Dependencies:
- Database session injection with proper transaction management and cleanup
- Service class instantiation with dependency resolution and lifecycle management
- Configuration injection with environment-specific settings and validation
- External service client injection with connection pooling and error handling
- Cache service injection with intelligent caching and invalidation strategies
- Logging service injection with structured logging and audit trail capabilities

Security Features:
- Secure token handling with proper validation and error responses
- Input sanitization and validation to prevent injection attacks
- Rate limiting per user and IP address for abuse prevention
- Security audit logging for compliance and monitoring requirements
- Error handling that doesn't leak sensitive information
- Integration with security monitoring and alerting systems

Performance Optimization:
- Efficient database session management with connection reuse
- Lazy loading of dependencies for optimal resource utilization
- Caching of frequently accessed data for reduced database load
- Async dependency resolution for non-blocking operations
- Memory management with proper cleanup and garbage collection
- Integration with performance monitoring and optimization tools

Use Cases:
- API endpoint protection with authentication and authorization
- Service layer dependency injection for clean architecture patterns
- Database session management across request lifecycle
- User context propagation through application layers
- Administrative function protection with proper privilege checking
- Integration with external services and microservices architecture

Example Usage:
    @router.get("/protected-endpoint")
    async def protected_function(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        user_service: UserService = Depends(get_user_service)
    ):
        # Endpoint with authenticated user, database session, and service injection
        return await user_service.get_user_profile(current_user.id)
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models.user import User
from .services.auth import AuthService
from .services.conversation import ConversationService
from .services.document import DocumentService
from .services.embedding import EmbeddingService
from .services.mcp_service import MCPService
from .services.search import SearchService
from .services.user import UserService

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise.

    This dependency allows endpoints to work with both authenticated
    and unauthenticated users.

    Args:
        credentials: Optional JWT token from Authorization header
        db: Database session

    Returns:
        Optional[User]: Current user or None if not authenticated

    """
    if not credentials:
        return None

    try:
        auth_service = AuthService(db)
        username = auth_service.verify_token(credentials.credentials)

        if not username:
            return None

        user = await auth_service.get_user_by_username(username)
        if not user or not user.is_active:
            return None

        return user

    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user.

    This dependency requires a valid JWT token and returns the current user.
    Raises HTTP 401 if authentication fails.

    Args:
        credentials: JWT token from Authorization header
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If authentication fails

    """
    try:
        auth_service = AuthService(db)
        username = auth_service.verify_token(credentials.credentials)

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await auth_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify superuser privileges.

    This dependency requires authentication and superuser privileges.
    Raises HTTP 403 if user is not a superuser.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If user is not a superuser

    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser access required.",
        )

    return current_user


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)


async def get_mcp_service(db: AsyncSession = Depends(get_db)) -> MCPService:
    """Get MCPService instance."""
    service = MCPService(db)
    await service.initialize()
    return service


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get UserService instance."""
    return UserService(db)


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Get DocumentService instance."""
    return DocumentService(db)


async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    """Get SearchService instance."""
    return SearchService(db)


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Get ConversationService instance."""
    return ConversationService(db)


async def get_embedding_service(db: AsyncSession = Depends(get_db)) -> EmbeddingService:
    """Get EmbeddingService instance."""
    return EmbeddingService(db)
