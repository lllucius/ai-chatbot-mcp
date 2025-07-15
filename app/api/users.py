"""
User management API endpoints.

This module provides endpoints for user profile management,
user administration, and user-related operations.

Generated on: 2025-07-14 03:12:05 UTC
Current User: lllucius
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.user import (
    UserResponse, 
    UserUpdate, 
    UserPasswordUpdate
)
from ..schemas.common import BaseResponse, PaginatedResponse
from ..services.user import UserService
from ..core.exceptions import NotFoundError, ValidationError, AuthorizationError
from ..dependencies import get_current_user, get_current_superuser

router = APIRouter(prefix="/users", tags=["users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user profile with statistics.
    
    Returns detailed profile information including
    document and conversation statistics.
    """
    try:
        profile = await user_service.get_user_profile(current_user.id)
        return profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    request: UserUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile.
    
    Allows users to update their own profile information
    such as email and full name.
    """
    try:
        updated_user = await user_service.update_user(current_user.id, request)
        return UserResponse.model_validate(updated_user)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.post("/me/change-password", response_model=BaseResponse)
async def change_password(
    request: UserPasswordUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change current user password.
   
    Requires the current password for verification
    and the new password.
    """ 
    try:
        success = await user_service.change_password(
            current_user.id,
            request.current_password,
            request.new_password
        )
        
        if success:
            return BaseResponse(
                success=True,
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
            
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Admin endpoints (require superuser privileges)

@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    superuser_only: bool = Query(False),
    current_user = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """
    List all users (admin only).
    
    Returns paginated list of users with optional filtering.
    Requires superuser privileges.
    """
    try:
        users, total = await user_service.list_users(
            page=page,
            size=size,
            active_only=active_only,
            superuser_only=superuser_only
        )
        
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        return PaginatedResponse.create(
            items=user_responses,
            total=total,
            page=page,
            size=size,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID (admin only).
    
    Returns detailed user information including statistics.
    Requires superuser privileges.
    """
    try:
        profile = await user_service.get_user_profile(user_id)
        return profile
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID (admin only).
    
    Allows administrators to update any user's profile.
    Requires superuser privileges.
    """
    try:
        updated_user = await user_service.update_user(user_id, request)
        return UserResponse.model_validate(updated_user)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: int,
    current_user = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID (admin only).
    
    Permanently deletes a user and all associated data.
    Requires superuser privileges.
    """
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = await user_service.delete_user(user_id)
        
        if success:
            return BaseResponse(
                success=True,
                message="User deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )
