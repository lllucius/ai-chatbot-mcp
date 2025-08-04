"""Pydantic schemas for analytics APIs.

This module provides analytics response schemas for system metrics,
usage statistics, and performance monitoring.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseModelSchema


class AnalyticsOverviewResponse(BaseModelSchema):
    """Analytics overview response schema."""

    users: Dict[str, Any] = Field(..., description="User statistics")
    documents: Dict[str, Any] = Field(..., description="Document statistics")
    conversations: Dict[str, Any] = Field(..., description="Conversation statistics")
    system_health: Dict[str, Any] = Field(..., description="System health metrics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class AnalyticsUsageResponse(BaseModelSchema):
    """Analytics usage response schema."""

    usage: Dict[str, Any] = Field(..., description="Usage statistics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class AnalyticsPerformanceResponse(BaseModelSchema):
    """Analytics performance response schema."""

    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class AnalyticsTrendsResponse(BaseModelSchema):
    """Analytics trends response schema."""

    trends: Dict[str, Any] = Field(..., description="Trend data")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class AnalyticsUserAnalyticsResponse(BaseModelSchema):
    """Analytics user analytics response schema."""

    user_analytics: Dict[str, Any] = Field(..., description="User analytics data")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class AnalyticsExportResponse(BaseModelSchema):
    """Analytics export response schema."""

    export_data: Dict[str, Any] = Field(..., description="Exported analytics data")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")