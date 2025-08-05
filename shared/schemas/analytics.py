"""Pydantic schemas for analytics APIs.

This module provides analytics response schemas for system metrics,
usage statistics, and performance monitoring.
"""

from typing import Any, Dict

from pydantic import Field

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

class SystemHealthScore(BaseModel):
    score: float = Field(..., description="Overall health score")
    factors: dict = Field(..., description="Health factors breakdown")


class UsersOverview(BaseModel):
    total: int = Field(..., description="Total users")
    active: int = Field(..., description="Active users")
    activity_rate: float = Field(..., description="User activity rate (%)")


class DocumentsOverview(BaseModel):
    total: int = Field(..., description="Total documents")
    processed: int = Field(..., description="Processed documents")
    processing_rate: float = Field(..., description="Document processing rate (%)")


class ConversationsOverview(BaseModel):
    total: int = Field(..., description="Total conversations")


class AnalyticsOverviewPayload(BaseModel):
    users: UsersOverview = Field(..., description="User stats")
    documents: DocumentsOverview = Field(..., description="Document stats")
    conversations: ConversationsOverview = Field(..., description="Conversation stats")
    system_health: SystemHealthScore = Field(..., description="System health score")
    timestamp: str = Field(..., description="Timestamp")


class UsageMetrics(BaseModel):
    new_users: int = Field(..., description="New users")
    new_documents: int = Field(..., description="New documents")
    new_conversations: int = Field(..., description="New conversations")
    total_messages: int = Field(..., description="Total messages")
    avg_messages_per_day: float = Field(..., description="Average messages per day")


class DailyStat(BaseModel):
    date: str = Field(..., description="Date")
    messages: int = Field(..., description="Messages on that date")


class AnalyticsUsagePayload(BaseModel):
    period: str = Field(..., description="Period string")
    start_date: str = Field(..., description="Period start date")
    end_date: str = Field(..., description="Period end date")
    metrics: UsageMetrics = Field(..., description="Metrics")
    daily_breakdown: Optional[List[DailyStat]] = Field(
        None, description="Daily breakdown"
    )


class DocumentProcessingPerformance(BaseModel):
    total_documents: int = Field(..., description="Total documents")
    completed: int = Field(..., description="Completed documents")
    failed: int = Field(..., description="Failed documents")
    processing: int = Field(..., description="Processing documents")
    success_rate: float = Field(..., description="Success rate (%)")
    failure_rate: float = Field(..., description="Failure rate (%)")


class DBPerformanceEntry(BaseModel):
    schemaname: Optional[str] = Field(None, description="Schema name")
    tablename: Optional[str] = Field(None, description="Table name")
    total_operations: Optional[int] = Field(None, description="Total operations")
    live_tuples: Optional[int] = Field(None, description="Live tuples")
    dead_tuples: Optional[int] = Field(None, description="Dead tuples")


class SystemMetricsInfo(BaseModel):
    timestamp: str = Field(..., description="Timestamp")
    health_status: str = Field(..., description="Health status")


class AnalyticsPerformancePayload(BaseModel):
    document_processing: DocumentProcessingPerformance = Field(..., description="Document processing stats")
    database_performance: List[DBPerformanceEntry] = Field(..., description="Database performance metrics")
    system_metrics: SystemMetricsInfo = Field(..., description="System metrics")


class TopUser(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    count: int = Field(..., description="Metric count")


class AnalyticsUserAnalyticsPayload(BaseModel):
    metric: str = Field(..., description="Metric analyzed")
    period: str = Field(..., description="Period")
    top_users: List[TopUser] = Field(..., description="Top users")
    total_returned: int = Field(..., description="Total users returned")
    generated_at: str = Field(..., description="Generated timestamp")


class DailyTrend(BaseModel):
    date: str = Field(..., description="Date")
    new_users: int = Field(..., description="New users")
    new_documents: int = Field(..., description="New documents")
    messages: int = Field(..., description="Messages")


class TrendSummary(BaseModel):
    total_new_users: int = Field(..., description="Total new users")
    total_new_documents: int = Field(..., description="Total new documents")
    total_messages: int = Field(..., description="Total messages")
    weekly_growth_rate: float = Field(..., description="Weekly growth rate (%)")


class AnalyticsTrendsPayload(BaseModel):
    period_days: int = Field(..., description="Period days")
    daily_trends: List[DailyTrend] = Field(..., description="Daily trends")
    summary: TrendSummary = Field(..., description="Summary")
    generated_at: str = Field(..., description="Generated timestamp")


class DetailedUserAnalyticsPayload(BaseModel):
    top_by_messages: Optional[List[TopUser]] = Field(None, description="Top users by messages")
    top_by_documents: Optional[List[TopUser]] = Field(None, description="Top users by documents")
    top_by_conversations: Optional[List[TopUser]] = Field(None, description="Top users by conversations")


class AnalyticsExportPayload(BaseModel):
    report_metadata: dict = Field(..., description="Report metadata")
    system_overview: AnalyticsOverviewPayload = Field(..., description="System overview")
    usage_statistics: AnalyticsUsagePayload = Field(..., description="Usage statistics")
    performance_metrics: AnalyticsPerformancePayload = Field(..., description="Performance metrics")
    usage_trends: AnalyticsTrendsPayload = Field(..., description="Usage trends")
    detailed_user_analytics: Optional[DetailedUserAnalyticsPayload] = Field(
        None, description="Detailed user analytics"
    )

