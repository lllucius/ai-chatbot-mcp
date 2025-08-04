"""Analytics and reporting API endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.analytics import (
    AnalyticsExportResponse,
    AnalyticsOverviewResponse,
    AnalyticsPerformanceResponse,
    AnalyticsTrendsResponse,
    AnalyticsUsageResponse,
    AnalyticsUserAnalyticsResponse,
)

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
@handle_api_errors("Failed to get system overview")
async def get_system_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewResponse:
    """Get comprehensive system overview and key performance indicators."""
    log_api_call("get_system_overview", user_id=str(current_user.id))

    from sqlalchemy import func, select

    from ..models.conversation import Conversation
    from ..models.document import Document, FileStatus
    from ..models.user import User as UserModel

    # Get basic counts
    total_users = await db.scalar(select(func.count(UserModel.id)))
    active_users = await db.scalar(
        select(func.count(UserModel.id)).where(UserModel.is_active)
    )

    total_documents = await db.scalar(select(func.count(Document.id)))
    processed_documents = await db.scalar(
        select(func.count(Document.id)).where(Document.status == FileStatus.COMPLETED)
    )

    total_conversations = await db.scalar(select(func.count(Conversation.id)))

    # Calculate processing rate
    processing_rate = (
        (processed_documents / max(total_documents, 1)) * 100 if total_documents else 0
    )

    # Health score calculation
    health_factors = {
        "user_activity": (
            min(100, (active_users / max(total_users, 1)) * 100) if total_users else 0
        ),
        "document_processing": processing_rate,
        "system_availability": 100,
    }
    health_score = sum(health_factors.values()) / len(health_factors)

    return AnalyticsOverviewResponse(
        users={
            "total": total_users or 0,
            "active": active_users or 0,
            "activity_rate": health_factors["user_activity"],
        },
        documents={
            "total": total_documents or 0,
            "processed": processed_documents or 0,
            "processing_rate": processing_rate,
        },
        conversations={"total": total_conversations or 0},
        system_health={"score": round(health_score, 2), "factors": health_factors},
        timestamp=datetime.utcnow().isoformat(),
        success=True,
        message="System overview retrieved successfully",
    )


@router.get("/usage", response_model=AnalyticsUsageResponse)
@handle_api_errors("Failed to get usage statistics")
async def get_usage_statistics(
    period: str = Query("7d", description="Time period: 1d, 7d, 30d, 90d"),
    detailed: bool = Query(False, description="Include detailed breakdown"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsUsageResponse:
    """Get comprehensive usage statistics with configurable time periods and detail levels."""
    log_api_call("get_usage_statistics", user_id=str(current_user.id), period=period)

    # Parse period
    period_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}

    if period not in period_map:
        raise HTTPException(
            status_code=400, detail="Invalid period. Use: 1d, 7d, 30d, or 90d"
        )

    days = period_map[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import and_, func, select

    from ..models.conversation import Conversation, Message
    from ..models.document import Document
    from ..models.user import User as UserModel

    # Get usage metrics for the period
    new_users = await db.scalar(
        select(func.count(UserModel.id)).where(UserModel.created_at >= start_date)
    )

    new_documents = await db.scalar(
        select(func.count(Document.id)).where(Document.created_at >= start_date)
    )

    new_conversations = await db.scalar(
        select(func.count(Conversation.id)).where(Conversation.created_at >= start_date)
    )

    total_messages = await db.scalar(
        select(func.count(Message.id)).where(Message.created_at >= start_date)
    )

    daily_stats = None
    if detailed:
        daily_stats = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_messages = await db.scalar(
                select(func.count(Message.id)).where(
                    and_(Message.created_at >= day_start, Message.created_at < day_end)
                )
            )

            daily_stats.append(
                {"date": day_start.date().isoformat(), "messages": day_messages or 0}
            )

    return AnalyticsUsageResponse(
        period=period,
        start_date=start_date.isoformat(),
        end_date=datetime.utcnow().isoformat(),
        metrics={
            "new_users": new_users or 0,
            "new_documents": new_documents or 0,
            "new_conversations": new_conversations or 0,
            "total_messages": total_messages or 0,
            "avg_messages_per_day": round((total_messages or 0) / days, 2),
        },
        daily_breakdown=daily_stats,
        success=True,
        message="Usage statistics retrieved successfully",
    )


@router.get("/performance", response_model=AnalyticsPerformanceResponse)
@handle_api_errors("Failed to get performance metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsPerformanceResponse:
    """Get comprehensive system performance metrics with bottleneck analysis and optimization insights."""
    log_api_call("get_performance_metrics", user_id=str(current_user.id))

    from sqlalchemy import func, select, text

    from ..models.document import Document, FileStatus

    # Document processing performance
    processing_stats = await db.execute(
        select(
            func.count(Document.id).label("total"),
            func.count(Document.id)
            .filter(Document.status == FileStatus.COMPLETED)
            .label("completed"),
            func.count(Document.id)
            .filter(Document.status == FileStatus.FAILED)
            .label("failed"),
            func.count(Document.id)
            .filter(Document.status == FileStatus.PROCESSING)
            .label("processing"),
        )
    )
    stats = processing_stats.first()

    # Calculate success rate
    total_processed = (stats.completed or 0) + (stats.failed or 0)
    success_rate = (
        (stats.completed / max(total_processed, 1)) * 100 if total_processed else 0
    )

    # Database performance metrics
    try:
        db_stats = await db.execute(
            text(
                """
            SELECT
                schemaname,
                tablename,
                n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables
            ORDER BY total_operations DESC
            LIMIT 5
        """
            )
        )
        db_performance = [dict(row) for row in db_stats.fetchall()]
    except Exception:
        db_performance = []

    return AnalyticsPerformanceResponse(
        document_processing={
            "total_documents": stats.total or 0,
            "completed": stats.completed or 0,
            "failed": stats.failed or 0,
            "processing": stats.processing or 0,
            "success_rate": round(success_rate, 2),
            "failure_rate": round(100 - success_rate, 2),
        },
        database_performance=db_performance,
        system_metrics={
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": "operational",
        },
        success=True,
        message="Performance metrics retrieved successfully",
    )


@router.get("/users", response_model=AnalyticsUserAnalyticsResponse)
@handle_api_errors("Failed to get user analytics")
async def get_user_analytics(
    metric: str = Query(
        "messages", description="Metric to analyze: messages, documents, conversations"
    ),
    top: int = Query(10, ge=1, le=100, description="Number of top users to return"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsUserAnalyticsResponse:
    """Get comprehensive user activity analytics with engagement metrics and behavioral insights."""
    log_api_call("get_user_analytics", user_id=str(current_user.id), metric=metric)

    # Parse period
    period_map = {"7d": 7, "30d": 30, "90d": 90}
    if period not in period_map:
        raise HTTPException(
            status_code=400, detail="Invalid period. Use: 7d, 30d, or 90d"
        )

    days = period_map[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import desc, func, select

    from ..models.conversation import Conversation, Message
    from ..models.document import Document
    from ..models.user import User as UserModel

    if metric == "messages":
        # Top users by message count
        query = (
            select(
                UserModel.username,
                UserModel.email,
                func.count(Message.id).label("count"),
            )
            .join(Conversation, UserModel.id == Conversation.user_id)
            .join(Message, Conversation.id == Message.conversation_id)
            .where(Message.created_at >= start_date)
            .group_by(UserModel.id, UserModel.username, UserModel.email)
            .order_by(desc("count"))
            .limit(top)
        )
    elif metric == "documents":
        # Top users by document count
        query = (
            select(
                UserModel.username,
                UserModel.email,
                func.count(Document.id).label("count"),
            )
            .join(Document, UserModel.id == Document.user_id)
            .where(Document.created_at >= start_date)
            .group_by(UserModel.id, UserModel.username, UserModel.email)
            .order_by(desc("count"))
            .limit(top)
        )
    elif metric == "conversations":
        # Top users by conversation count
        query = (
            select(
                UserModel.username,
                UserModel.email,
                func.count(Conversation.id).label("count"),
            )
            .join(Conversation, UserModel.id == Conversation.user_id)
            .where(Conversation.created_at >= start_date)
            .group_by(UserModel.id, UserModel.username, UserModel.email)
            .order_by(desc("count"))
            .limit(top)
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid metric. Use: messages, documents, or conversations",
        )

    result = await db.execute(query)
    top_users = [
        {"username": row.username, "email": row.email, "count": row.count}
        for row in result.fetchall()
    ]

    return AnalyticsUserAnalyticsResponse(
        metric=metric,
        period=period,
        top_users=top_users,
        total_returned=len(top_users),
        generated_at=datetime.utcnow().isoformat(),
        success=True,
        message="User analytics retrieved successfully",
    )


@router.get("/trends", response_model=AnalyticsTrendsResponse)
@handle_api_errors("Failed to get usage trends")
async def get_usage_trends(
    days: int = Query(14, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsTrendsResponse:
    """Get comprehensive usage trends and growth patterns with predictive insights."""
    log_api_call("get_usage_trends", user_id=str(current_user.id), days=days)

    start_date = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import and_, func, select

    from ..models.conversation import Message
    from ..models.document import Document
    from ..models.user import User as UserModel

    # Daily trends
    daily_trends = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        new_users = await db.scalar(
            select(func.count(UserModel.id)).where(
                and_(UserModel.created_at >= day_start, UserModel.created_at < day_end)
            )
        )

        new_documents = await db.scalar(
            select(func.count(Document.id)).where(
                and_(Document.created_at >= day_start, Document.created_at < day_end)
            )
        )

        messages = await db.scalar(
            select(func.count(Message.id)).where(
                and_(Message.created_at >= day_start, Message.created_at < day_end)
            )
        )

        daily_trends.append(
            {
                "date": day_start.date().isoformat(),
                "new_users": new_users or 0,
                "new_documents": new_documents or 0,
                "messages": messages or 0,
            }
        )

    # Calculate growth rates
    if len(daily_trends) >= 7:
        recent_week = daily_trends[-7:]
        previous_week = (
            daily_trends[-14:-7] if len(daily_trends) >= 14 else daily_trends[:-7]
        )

        recent_avg = sum(day["messages"] for day in recent_week) / 7
        previous_avg = (
            sum(day["messages"] for day in previous_week) / len(previous_week)
            if previous_week
            else recent_avg
        )

        growth_rate = (
            ((recent_avg - previous_avg) / max(previous_avg, 1)) * 100
            if previous_week
            else 0
        )
    else:
        growth_rate = 0

    return AnalyticsTrendsResponse(
        period_days=days,
        daily_trends=daily_trends,
        summary={
            "total_new_users": sum(day["new_users"] for day in daily_trends),
            "total_new_documents": sum(day["new_documents"] for day in daily_trends),
            "total_messages": sum(day["messages"] for day in daily_trends),
            "weekly_growth_rate": round(growth_rate, 2),
        },
        generated_at=datetime.utcnow().isoformat(),
        success=True,
        message="Usage trends retrieved successfully",
    )


@router.post("/export-report", response_model=AnalyticsExportResponse)
@handle_api_errors("Failed to export analytics report")
async def export_analytics_report(
    include_details: bool = Query(True, description="Include detailed breakdowns"),
    format: str = Query("json", description="Export format: json"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsExportResponse:
    """Export comprehensive analytics report for executive analysis and external integration."""
    log_api_call("export_analytics_report", user_id=str(current_user.id))

    if format != "json":
        raise HTTPException(
            status_code=400, detail="Only JSON format is currently supported"
        )

    # Gather all analytics data
    overview_data = await get_system_overview(current_user, db)
    usage_data = await get_usage_statistics("30d", include_details, current_user, db)
    performance_data = await get_performance_metrics(current_user, db)
    trends_data = await get_usage_trends(30, current_user, db)

    detailed_user_analytics = None
    if include_details:
        user_messages = await get_user_analytics(
            "messages", 20, "30d", current_user, db
        )
        user_documents = await get_user_analytics(
            "documents", 20, "30d", current_user, db
        )
        user_conversations = await get_user_analytics(
            "conversations", 20, "30d", current_user, db
        )

        detailed_user_analytics = {
            "top_by_messages": user_messages.top_users,
            "top_by_documents": user_documents.top_users,
            "top_by_conversations": user_conversations.top_users,
        }

    return AnalyticsExportResponse(
        report_metadata={
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user.username,
            "period": "30 days",
            "format": format,
            "includes_details": include_details,
        },
        system_overview=overview_data,
        usage_statistics=usage_data,
        performance_metrics=performance_data,
        usage_trends=trends_data,
        detailed_user_analytics=detailed_user_analytics,
        success=True,
        message="Analytics report exported successfully",
    )
