"""
FastAPI dependencies for authentication and authorization.

This module provides reusable dependencies for FastAPI endpoints
including user authentication, authorization checks, and common utilities.

"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models.user import User
from .services.auth import AuthService

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

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
    """
    Get current authenticated user.

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
    """
    Get current user and verify superuser privileges.

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
