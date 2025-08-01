"""
Pydantic schemas for analytics/reporting endpoints.

Defines explicit response schemas for system analytics,
usage statistics, trends, performance, and export endpoints.
All fields explicitly specify the 'description' argument.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    """Response schema for system overview analytics."""
    users: Dict[str, Any] = Field(..., description="User statistics block")
    documents: Dict[str, Any] = Field(..., description="Document statistics block")
    conversations: Dict[str, Any] = Field(..., description="Conversation statistics block")
    system_health: Dict[str, Any] = Field(..., description="System health block")
    timestamp: str = Field(..., description="Timestamp the data was generated")
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")


class AnalyticsUsageResponse(BaseModel):
    """Response schema for usage statistics."""
    period: str = Field(..., description="Usage period string (e.g., 7d)")
    start_date: str = Field(..., description="Period start date (ISO-8601)")
    end_date: str = Field(..., description="Period end date (ISO-8601)")
    metrics: Dict[str, Any] = Field(..., description="Metrics for the time period")
    daily_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, description="Breakdown of statistics per day"
    )
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")


class AnalyticsPerformanceResponse(BaseModel):
    """Response schema for performance metrics."""
    document_processing: Dict[str, Any] = Field(..., description="Document processing stats")
    database_performance: List[Dict[str, Any]] = Field(..., description="Database performance info")
    system_metrics: Dict[str, Any] = Field(..., description="System metrics summary")
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")


class AnalyticsUserAnalyticsResponse(BaseModel):
    """Response schema for user analytics."""
    metric: str = Field(..., description="Metric used for analytics (messages, documents, conversations)")
    period: str = Field(..., description="Time period for analytics (e.g., 30d)")
    top_users: List[Dict[str, Any]] = Field(..., description="List of top users by metric")
    total_returned: int = Field(..., description="Number of users returned")
    generated_at: str = Field(..., description="Timestamp analytics were generated")
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")


class AnalyticsTrendsResponse(BaseModel):
    """Response schema for usage trends."""
    period_days: int = Field(..., description="Number of days in analysis")
    daily_trends: List[Dict[str, Any]] = Field(..., description="List of daily trend objects")
    summary: Dict[str, Any] = Field(..., description="Summary with totals/growth rate")
    generated_at: str = Field(..., description="Timestamp analytics were generated")
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")


class AnalyticsExportResponse(BaseModel):
    """Response schema for analytics export."""
    report_metadata: Dict[str, Any] = Field(..., description="Metadata about the report")
    system_overview: AnalyticsOverviewResponse = Field(..., description="System overview block")
    usage_statistics: AnalyticsUsageResponse = Field(..., description="Usage statistics block")
    performance_metrics: AnalyticsPerformanceResponse = Field(..., description="Performance metrics block")
    usage_trends: AnalyticsTrendsResponse = Field(..., description="Usage trends block")
    detailed_user_analytics: Optional[Dict[str, Any]] = Field(
        None, description="Detailed user analytics if included"
    )
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(..., description="Status message")