"""
Authentication service for user management and JWT token handling.

This service provides methods for user registration, authentication,
password management, and JWT token creation/verification.

Generated on: 2025-07-14 03:08:19 UTC
Current User: lllucius
"""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.exceptions import AuthenticationError, ValidationError
from ..models.user import User
from ..schemas.auth import RegisterRequest, Token
from ..utils.security import get_password_hash, verify_password
from ..utils.timestamp import utcnow

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service for user management and JWT operations.

    This service handles user registration, authentication, password management,
    and JWT token creation and verification.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize authentication service.

        Args:
            db: Database session for user operations
        """
        self.db = db
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    async def register_user(self, user_data: RegisterRequest) -> User:
        """
        Register a new user account.

        Args:
            user_data: User registration data

        Returns:
            User: Created user object

        Raises:
            ValidationError: If username or email already exists
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
        """
        Authenticate user with username and password.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Token: JWT token data

        Raises:
            AuthenticationError: If authentication fails
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
            print("USERID", user.id)
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
        """
        Create JWT access token.

        Args:
            data: Token payload data

        Returns:
            Token: JWT token with expiration info
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
        """
        Verify JWT token and extract username.

        Args:
            token: JWT token string

        Returns:
            str: Username from token payload, None if invalid
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
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User: User object or None if not found
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User: User object or None if not found
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID to search for

        Returns:
            User: User object or None if not found
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
