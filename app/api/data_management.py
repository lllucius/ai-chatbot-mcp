"""Data Management API endpoints for bulk operations."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_superuser
from app.models.user import User
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.common import APIResponse

router = APIRouter(tags=["data-management"])


@router.post("/bulk/delete-documents")
@handle_api_errors("Failed to bulk delete documents")
async def bulk_delete_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to delete"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Bulk delete multiple documents."""
    log_api_call("bulk_delete_documents", user_id=str(current_user.id), count=len(document_ids))
    
    # Mock deletion - in real implementation this would use a service
    result = {
        "deleted_count": len(document_ids),
        "failed_count": 0,
        "deleted_ids": document_ids,
        "failed_ids": [],
        "operation_id": f"bulk-delete-docs-{len(document_ids)}"
    }
    
    return APIResponse[dict](
        success=True,
        message=f"Successfully deleted {len(document_ids)} documents",
        data=result,
    )


@router.post("/bulk/delete-conversations")
@handle_api_errors("Failed to bulk delete conversations")
async def bulk_delete_conversations(
    conversation_ids: List[str] = Query(..., description="List of conversation IDs to delete"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Bulk delete multiple conversations."""
    log_api_call("bulk_delete_conversations", user_id=str(current_user.id), count=len(conversation_ids))
    
    # Mock deletion - in real implementation this would use a service
    result = {
        "deleted_count": len(conversation_ids),
        "failed_count": 0,
        "deleted_ids": conversation_ids,
        "failed_ids": [],
        "operation_id": f"bulk-delete-convs-{len(conversation_ids)}"
    }
    
    return APIResponse[dict](
        success=True,
        message=f"Successfully deleted {len(conversation_ids)} conversations",
        data=result,
    )


@router.post("/bulk/delete-prompts")
@handle_api_errors("Failed to bulk delete prompts")
async def bulk_delete_prompts(
    prompt_ids: List[str] = Query(..., description="List of prompt IDs to delete"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Bulk delete multiple prompts."""
    log_api_call("bulk_delete_prompts", user_id=str(current_user.id), count=len(prompt_ids))
    
    # Mock deletion - in real implementation this would use a service
    result = {
        "deleted_count": len(prompt_ids),
        "failed_count": 0,
        "deleted_ids": prompt_ids,
        "failed_ids": [],
        "operation_id": f"bulk-delete-prompts-{len(prompt_ids)}"
    }
    
    return APIResponse[dict](
        success=True,
        message=f"Successfully deleted {len(prompt_ids)} prompts",
        data=result,
    )