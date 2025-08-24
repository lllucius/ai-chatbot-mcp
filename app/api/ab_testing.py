"""A/B Testing API endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.common import APIResponse

router = APIRouter(tags=["ab-testing"])


@router.get("/{test_id}/performance")
@handle_api_errors("Failed to get A/B test performance")
async def get_test_performance(
    test_id: str,
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:
    """Get performance metrics for an A/B test."""
    log_api_call("get_test_performance", user_id=str(current_user.id), test_id=test_id)
    
    # Mock performance data - in real implementation this would come from a service
    performance_data = {
        "test_id": test_id,
        "variant_a": {
            "conversion_rate": 0.125,
            "sample_size": 1000,
            "confidence_interval": [0.105, 0.145]
        },
        "variant_b": {
            "conversion_rate": 0.138,
            "sample_size": 1000,
            "confidence_interval": [0.118, 0.158]
        },
        "statistical_significance": 0.85,
        "status": "running"
    }
    
    return APIResponse[dict](
        success=True,
        message="A/B test performance retrieved successfully",
        data=performance_data,
    )