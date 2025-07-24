"API endpoints for users operations."

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.exceptions import NotFoundError, ValidationError
from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..schemas.common import BaseResponse, PaginatedResponse
from ..schemas.user import UserPasswordUpdate, UserResponse, UserUpdate
from ..services.user import UserService
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    "Get user service data."
    return UserService(db)


@router.get("/me", response_model=UserResponse)
@handle_api_errors("Failed to retrieve user profile")
async def get_my_profile(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    "Get my profile data."
    log_api_call("get_my_profile", user_id=str(current_user.id))
    profile = await user_service.get_user_profile(current_user.id)
    return profile


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    request: UserUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    "Update existing my profile."
    try:
        updated_user = await user_service.update_user(current_user.id, request)
        return UserResponse.model_validate(updated_user)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )


@router.post("/me/change-password", response_model=BaseResponse)
async def change_password(
    request: UserPasswordUpdate,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    "Change Password operation."
    try:
        success = await user_service.change_password(
            current_user.id, request.current_password, request.new_password
        )
        if success:
            return BaseResponse(success=True, message="Password changed successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    superuser_only: bool = Query(False),
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    "List users entries."
    try:
        (users, total) = await user_service.list_users(
            page=page, size=size, active_only=active_only, superuser_only=superuser_only
        )
        user_responses = [UserResponse.model_validate(user) for user in users]
        return PaginatedResponse.create(
            items=user_responses,
            total=total,
            page=page,
            size=size,
            message="Users retrieved successfully",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    "Get user data."
    try:
        profile = await user_service.get_user_profile(user_id)
        return profile
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    "Update existing user."
    try:
        updated_user = await user_service.update_user(user_id, request)
        return UserResponse.model_validate(updated_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed",
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service),
):
    "Delete user."
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )
        success = await user_service.delete_user(user_id)
        if success:
            return BaseResponse(success=True, message="User deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed",
        )
