"""
Analytics and reporting CLI commands.

Provides comprehensive analytics functionality including:
- Usage statistics and trends
- Performance metrics
- User activity reports
- Document processing analytics
- System health monitoring
"""

from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import and_, desc, func, select

from ..database import AsyncSessionLocal
from ..models.conversation import Conversation, Message
from ..models.document import Document, DocumentChunk, FileStatus
from ..models.user import User
from .base import (
    async_command,
    console,
    error_message,
    format_size,
    info_message,
    success_message,
)

# Create the analytics app
analytics_app = typer.Typer(help="Analytics and reporting commands")


@analytics_app.command()
def overview():
    """Show system overview and key metrics."""

    @async_command
    async def _system_overview():
        async with AsyncSessionLocal() as db:
            try:
                # Get current timestamp
                now = datetime.now()
                last_24h = now - timedelta(hours=24)
                now - timedelta(days=7)
                now - timedelta(days=30)

                # User metrics
                total_users = await db.scalar(select(func.count(User.id)))
                active_users = await db.scalar(
                    select(func.count(User.id)).where(User.is_active)
                )
                new_users_24h = await db.scalar(
                    select(func.count(User.id)).where(User.created_at >= last_24h)
                )

                # Document metrics
                total_docs = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.status == FileStatus.COMPLETED
                    )
                )
                total_storage = await db.scalar(select(func.sum(Document.file_size)))
                docs_24h = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.created_at >= last_24h
                    )
                )

                # Conversation metrics
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                active_convs = await db.scalar(
                    select(func.count(Conversation.id)).where(Conversation.is_active)
                )
                total_messages = await db.scalar(select(func.count(Message.id)))
                messages_24h = await db.scalar(
                    select(func.count(Message.id)).where(Message.created_at >= last_24h)
                )

                # Create overview panels
                user_panel = Panel(
                    f"[bold green]Total:[/bold green] {total_users or 0}\n"
                    f"[bold blue]Active:[/bold blue] {active_users or 0}\n"
                    f"[bold yellow]New (24h):[/bold yellow] {new_users_24h or 0}",
                    title="👥 Users",
                    border_style="green",
                )

                doc_panel = Panel(
                    f"[bold green]Total:[/bold green] {total_docs or 0}\n"
                    f"[bold blue]Processed:[/bold blue] {completed_docs or 0}\n"
                    f"[bold yellow]Storage:[/bold yellow] {format_size(total_storage or 0)}\n"
                    f"[bold cyan]New (24h):[/bold cyan] {docs_24h or 0}",
                    title="📄 Documents",
                    border_style="blue",
                )

                conv_panel = Panel(
                    f"[bold green]Total:[/bold green] {total_convs or 0}\n"
                    f"[bold blue]Active:[/bold blue] {active_convs or 0}\n"
                    f"[bold yellow]Messages:[/bold yellow] {total_messages or 0}\n"
                    f"[bold cyan]Msgs (24h):[/bold cyan] {messages_24h or 0}",
                    title="💬 Conversations",
                    border_style="yellow",
                )

                # System health indicators
                processing_rate = (
                    ((completed_docs or 0) / max((total_docs or 1), 1)) * 100
                    if total_docs
                    else 0
                )
                user_activity = (
                    ((active_convs or 0) / max((total_convs or 1), 1)) * 100
                    if total_convs
                    else 0
                )

                health_indicators = []
                if processing_rate > 90:
                    health_indicators.append("🟢 Document Processing: Excellent")
                elif processing_rate > 70:
                    health_indicators.append("🟡 Document Processing: Good")
                else:
                    health_indicators.append("🔴 Document Processing: Needs Attention")

                if user_activity > 50:
                    health_indicators.append("🟢 User Engagement: High")
                elif user_activity > 20:
                    health_indicators.append("🟡 User Engagement: Moderate")
                else:
                    health_indicators.append("🔴 User Engagement: Low")

                health_panel = Panel(
                    "\n".join(health_indicators),
                    title="🔋 System Health",
                    border_style="cyan",
                )

                # Display overview
                console.print(
                    Panel(
                        f"[bold]AI Chatbot Platform Analytics[/bold]\n"
                        f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                        title="📊 System Overview",
                        border_style="bright_blue",
                    )
                )

                console.print(Columns([user_panel, doc_panel, conv_panel]))
                console.print(health_panel)

            except Exception as e:
                error_message(f"Failed to generate overview: {e}")

    _system_overview()


@analytics_app.command()
def usage(
    period: str = typer.Option(
        "7d", "--period", "-p", help="Time period: 1d, 7d, 30d, 90d"
    ),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed breakdown"
    ),
):
    """Show usage statistics for the specified period."""

    @async_command
    async def _usage_stats():
        async with AsyncSessionLocal() as db:
            try:
                # Parse period
                period_map = {
                    "1d": timedelta(days=1),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30),
                    "90d": timedelta(days=90),
                }

                if period not in period_map:
                    error_message(f"Invalid period: {period}. Use 1d, 7d, 30d, or 90d")
                    return

                cutoff_date = datetime.now() - period_map[period]

                # User activity
                active_users = await db.scalar(
                    select(func.count(func.distinct(Conversation.user_id))).where(
                        and_(
                            Conversation.created_at >= cutoff_date,
                            Conversation.user_id.isnot(None),
                        )
                    )
                )

                new_users = await db.scalar(
                    select(func.count(User.id)).where(User.created_at >= cutoff_date)
                )

                # Document activity
                new_documents = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.created_at >= cutoff_date
                    )
                )

                processed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        and_(
                            Document.updated_at >= cutoff_date,
                            Document.status == FileStatus.COMPLETED,
                        )
                    )
                )

                # Conversation activity
                new_conversations = await db.scalar(
                    select(func.count(Conversation.id)).where(
                        Conversation.created_at >= cutoff_date
                    )
                )

                new_messages = await db.scalar(
                    select(func.count(Message.id)).where(
                        Message.created_at >= cutoff_date
                    )
                )

                # Token usage
                tokens_used = await db.scalar(
                    select(func.sum(Message.token_count)).where(
                        Message.created_at >= cutoff_date
                    )
                )

                # Create usage table
                table = Table(title=f"Usage Statistics - Last {period}")
                table.add_column("Metric", style="cyan", width=25)
                table.add_column("Count", style="green", width=15)
                table.add_column("Daily Avg", style="yellow", width=12)

                days = period_map[period].days

                table.add_row(
                    "Active Users",
                    str(active_users or 0),
                    f"{(active_users or 0) / days:.1f}",
                )
                table.add_row(
                    "New Users", str(new_users or 0), f"{(new_users or 0) / days:.1f}"
                )
                table.add_row(
                    "New Documents",
                    str(new_documents or 0),
                    f"{(new_documents or 0) / days:.1f}",
                )
                table.add_row(
                    "Processed Documents",
                    str(processed_docs or 0),
                    f"{(processed_docs or 0) / days:.1f}",
                )
                table.add_row(
                    "New Conversations",
                    str(new_conversations or 0),
                    f"{(new_conversations or 0) / days:.1f}",
                )
                table.add_row(
                    "New Messages",
                    str(new_messages or 0),
                    f"{(new_messages or 0) / days:.1f}",
                )
                table.add_row(
                    "Tokens Used",
                    str(tokens_used or 0),
                    f"{(tokens_used or 0) / days:.0f}",
                )

                console.print(table)

                # Detailed breakdown if requested
                if detailed:
                    # Daily breakdown for shorter periods
                    if period in ["1d", "7d"]:
                        daily_table = Table(title="Daily Breakdown")
                        daily_table.add_column("Date", style="cyan")
                        daily_table.add_column("Users", style="green")
                        daily_table.add_column("Docs", style="blue")
                        daily_table.add_column("Convs", style="yellow")
                        daily_table.add_column("Msgs", style="magenta")

                        for i in range(days):
                            day_start = cutoff_date + timedelta(days=i)
                            day_end = day_start + timedelta(days=1)

                            daily_users = await db.scalar(
                                select(
                                    func.count(func.distinct(Conversation.user_id))
                                ).where(
                                    and_(
                                        Conversation.created_at >= day_start,
                                        Conversation.created_at < day_end,
                                        Conversation.user_id.isnot(None),
                                    )
                                )
                            )

                            daily_docs = await db.scalar(
                                select(func.count(Document.id)).where(
                                    and_(
                                        Document.created_at >= day_start,
                                        Document.created_at < day_end,
                                    )
                                )
                            )

                            daily_convs = await db.scalar(
                                select(func.count(Conversation.id)).where(
                                    and_(
                                        Conversation.created_at >= day_start,
                                        Conversation.created_at < day_end,
                                    )
                                )
                            )

                            daily_msgs = await db.scalar(
                                select(func.count(Message.id)).where(
                                    and_(
                                        Message.created_at >= day_start,
                                        Message.created_at < day_end,
                                    )
                                )
                            )

                            daily_table.add_row(
                                day_start.strftime("%m-%d"),
                                str(daily_users or 0),
                                str(daily_docs or 0),
                                str(daily_convs or 0),
                                str(daily_msgs or 0),
                            )

                        console.print(daily_table)

            except Exception as e:
                error_message(f"Failed to generate usage statistics: {e}")

    _usage_stats()


@analytics_app.command()
def performance():
    """Show system performance metrics."""

    @async_command
    async def _performance_metrics():
        async with AsyncSessionLocal() as db:
            try:
                # Document processing metrics
                total_docs = await db.scalar(select(func.count(Document.id)))
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.status == FileStatus.COMPLETED
                    )
                )
                processing_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.status == FileStatus.PROCESSING
                    )
                )
                failed_docs = await db.scalar(
                    select(func.count(Document.id)).where(
                        Document.status == FileStatus.FAILED
                    )
                )

                # Processing success rate
                success_rate = (
                    ((completed_docs or 0) / max((total_docs or 1), 1)) * 100
                    if total_docs
                    else 0
                )
                failure_rate = (
                    ((failed_docs or 0) / max((total_docs or 1), 1)) * 100
                    if total_docs
                    else 0
                )

                # Average document size and processing metrics
                avg_doc_size = await db.scalar(select(func.avg(Document.file_size)))
                total_chunks = await db.scalar(select(func.count(DocumentChunk.id)))
                avg_chunks_per_doc = (
                    (total_chunks or 0) / max((completed_docs or 1), 1)
                    if completed_docs
                    else 0
                )

                # Conversation metrics
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                avg_messages_per_conv = await db.scalar(
                    select(
                        func.avg(
                            select(func.count(Message.id))
                            .where(Message.conversation_id == Conversation.id)
                            .scalar_subquery()
                        )
                    )
                )

                # Token usage efficiency
                total_tokens = await db.scalar(select(func.sum(Message.token_count)))
                avg_tokens_per_message = await db.scalar(
                    select(func.avg(Message.token_count))
                )

                # Performance table
                table = Table(title="System Performance Metrics")
                table.add_column("Category", style="cyan", width=20)
                table.add_column("Metric", style="green", width=25)
                table.add_column("Value", style="yellow", width=15)
                table.add_column("Status", width=15)

                # Document processing performance
                status_icon = (
                    "🟢" if success_rate > 90 else "🟡" if success_rate > 70 else "🔴"
                )
                table.add_row(
                    "Document Processing",
                    "Success Rate",
                    f"{success_rate:.1f}%",
                    f"{status_icon} {'Excellent' if success_rate > 90 else 'Good' if success_rate > 70 else 'Poor'}",
                )
                table.add_row("", "Failure Rate", f"{failure_rate:.1f}%", "")
                table.add_row("", "Currently Processing", str(processing_docs or 0), "")
                table.add_row(
                    "", "Avg Document Size", format_size(avg_doc_size or 0), ""
                )
                table.add_row("", "Avg Chunks per Doc", f"{avg_chunks_per_doc:.1f}", "")

                # Conversation performance
                table.add_row("", "", "", "")  # Separator
                conv_efficiency = (
                    "🟢 High"
                    if avg_messages_per_conv and avg_messages_per_conv > 5
                    else "🟡 Moderate"
                )
                table.add_row(
                    "Conversations", "Total Conversations", str(total_convs or 0), ""
                )
                table.add_row(
                    "",
                    "Avg Messages/Conv",
                    f"{avg_messages_per_conv or 0:.1f}",
                    conv_efficiency,
                )
                table.add_row(
                    "",
                    "Total Messages",
                    str(await db.scalar(select(func.count(Message.id))) or 0),
                    "",
                )

                # Token efficiency
                table.add_row("", "", "", "")  # Separator
                token_efficiency = (
                    "🟢 Efficient"
                    if avg_tokens_per_message and avg_tokens_per_message < 500
                    else "🟡 Moderate"
                )
                table.add_row("Token Usage", "Total Tokens", str(total_tokens or 0), "")
                table.add_row(
                    "",
                    "Avg Tokens/Message",
                    f"{avg_tokens_per_message or 0:.0f}",
                    token_efficiency,
                )

                # Storage efficiency
                table.add_row("", "", "", "")  # Separator
                total_storage = await db.scalar(select(func.sum(Document.file_size)))
                user_count = await db.scalar(select(func.count(User.id)))
                storage_per_user = (
                    (total_storage or 0) / max((user_count or 1), 1)
                    if total_storage
                    else 0
                )
                table.add_row(
                    "Storage", "Total Storage", format_size(total_storage or 0), ""
                )
                table.add_row(
                    "", "Storage per User", format_size(int(storage_per_user)), ""
                )

                console.print(table)

                # Performance recommendations
                recommendations = []
                if success_rate < 80:
                    recommendations.append(
                        "Consider reviewing document processing pipeline"
                    )
                if failure_rate > 10:
                    recommendations.append("High failure rate - check error logs")
                if avg_tokens_per_message and avg_tokens_per_message > 1000:
                    recommendations.append(
                        "High token usage - consider response optimization"
                    )
                if processing_docs and processing_docs > 10:
                    recommendations.append(
                        "Many documents in processing queue - check background workers"
                    )

                if recommendations:
                    rec_panel = Panel(
                        "\n".join(f"• {rec}" for rec in recommendations),
                        title="🔧 Performance Recommendations",
                        border_style="yellow",
                    )
                    console.print(rec_panel)
                else:
                    success_message("System performance is optimal!")

            except Exception as e:
                error_message(f"Failed to generate performance metrics: {e}")

    _performance_metrics()


@analytics_app.command()
def users(
    top_n: int = typer.Option(10, "--top", "-n", help="Show top N users"),
    metric: str = typer.Option(
        "messages", "--metric", "-m", help="Sort by: messages, documents, conversations"
    ),
):
    """Show user activity analytics."""

    @async_command
    async def _user_analytics():
        async with AsyncSessionLocal() as db:
            try:
                if metric == "messages":
                    # Users by message count
                    query = (
                        select(
                            User.username,
                            User.email,
                            func.count(Message.id).label("message_count"),
                            func.sum(Message.token_count).label("total_tokens"),
                        )
                        .join(Conversation, User.id == Conversation.user_id)
                        .join(Message, Conversation.id == Message.conversation_id)
                        .group_by(User.id, User.username, User.email)
                        .order_by(desc("message_count"))
                        .limit(top_n)
                    )

                    result = await db.execute(query)
                    users = result.all()

                    table = Table(title=f"Top {top_n} Users by Messages")
                    table.add_column("Rank", style="cyan", width=6)
                    table.add_column("Username", style="green", width=20)
                    table.add_column("Messages", style="yellow", width=10)
                    table.add_column("Tokens", style="blue", width=12)
                    table.add_column("Avg Tokens/Msg", style="magenta", width=15)

                    for i, (username, email, msg_count, total_tokens) in enumerate(
                        users, 1
                    ):
                        avg_tokens = (
                            (total_tokens or 0) / max(msg_count, 1) if msg_count else 0
                        )
                        table.add_row(
                            str(i),
                            username,
                            str(msg_count),
                            str(total_tokens or 0),
                            f"{avg_tokens:.0f}",
                        )

                elif metric == "documents":
                    # Users by document count
                    query = (
                        select(
                            User.username,
                            User.email,
                            func.count(Document.id).label("doc_count"),
                            func.sum(Document.file_size).label("total_size"),
                        )
                        .join(Document, User.id == Document.owner_id)
                        .group_by(User.id, User.username, User.email)
                        .order_by(desc("doc_count"))
                        .limit(top_n)
                    )

                    result = await db.execute(query)
                    users = result.all()

                    table = Table(title=f"Top {top_n} Users by Documents")
                    table.add_column("Rank", style="cyan", width=6)
                    table.add_column("Username", style="green", width=20)
                    table.add_column("Documents", style="yellow", width=12)
                    table.add_column("Total Size", style="blue", width=12)
                    table.add_column("Avg Size", style="magenta", width=12)

                    for i, (username, email, doc_count, total_size) in enumerate(
                        users, 1
                    ):
                        avg_size = (
                            (total_size or 0) / max(doc_count, 1) if doc_count else 0
                        )
                        table.add_row(
                            str(i),
                            username,
                            str(doc_count),
                            format_size(total_size or 0),
                            format_size(avg_size),
                        )

                elif metric == "conversations":
                    # Users by conversation count
                    query = (
                        select(
                            User.username,
                            User.email,
                            func.count(Conversation.id).label("conv_count"),
                            func.avg(
                                select(func.count(Message.id))
                                .where(Message.conversation_id == Conversation.id)
                                .scalar_subquery()
                            ).label("avg_messages"),
                        )
                        .join(Conversation, User.id == Conversation.user_id)
                        .group_by(User.id, User.username, User.email)
                        .order_by(desc("conv_count"))
                        .limit(top_n)
                    )

                    result = await db.execute(query)
                    users = result.all()

                    table = Table(title=f"Top {top_n} Users by Conversations")
                    table.add_column("Rank", style="cyan", width=6)
                    table.add_column("Username", style="green", width=20)
                    table.add_column("Conversations", style="yellow", width=15)
                    table.add_column("Avg Msgs/Conv", style="blue", width=15)

                    for i, (username, email, conv_count, avg_messages) in enumerate(
                        users, 1
                    ):
                        table.add_row(
                            str(i),
                            username,
                            str(conv_count),
                            f"{avg_messages or 0:.1f}",
                        )

                else:
                    error_message(
                        f"Invalid metric: {metric}. Use messages, documents, or conversations"
                    )
                    return

                console.print(table)

            except Exception as e:
                error_message(f"Failed to generate user analytics: {e}")

    _user_analytics()


@analytics_app.command()
def trends(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
):
    """Show usage trends over time."""

    @async_command
    async def _usage_trends():
        async with AsyncSessionLocal() as db:
            try:
                start_date = datetime.now() - timedelta(days=days)

                # Weekly trends for longer periods, daily for shorter
                interval_days = 7 if days > 14 else 1
                intervals = days // interval_days

                trends_table = Table(title=f"Usage Trends - Last {days} Days")
                trends_table.add_column("Period", style="cyan", width=12)
                trends_table.add_column("New Users", style="green", width=12)
                trends_table.add_column("New Docs", style="blue", width=12)
                trends_table.add_column("New Convs", style="yellow", width=12)
                trends_table.add_column("Messages", style="magenta", width=12)
                trends_table.add_column("Tokens", style="red", width=12)

                for i in range(intervals):
                    period_start = start_date + timedelta(days=i * interval_days)
                    period_end = period_start + timedelta(days=interval_days)

                    # Get metrics for this period
                    new_users = await db.scalar(
                        select(func.count(User.id)).where(
                            and_(
                                User.created_at >= period_start,
                                User.created_at < period_end,
                            )
                        )
                    )

                    new_docs = await db.scalar(
                        select(func.count(Document.id)).where(
                            and_(
                                Document.created_at >= period_start,
                                Document.created_at < period_end,
                            )
                        )
                    )

                    new_convs = await db.scalar(
                        select(func.count(Conversation.id)).where(
                            and_(
                                Conversation.created_at >= period_start,
                                Conversation.created_at < period_end,
                            )
                        )
                    )

                    messages = await db.scalar(
                        select(func.count(Message.id)).where(
                            and_(
                                Message.created_at >= period_start,
                                Message.created_at < period_end,
                            )
                        )
                    )

                    tokens = await db.scalar(
                        select(func.sum(Message.token_count)).where(
                            and_(
                                Message.created_at >= period_start,
                                Message.created_at < period_end,
                            )
                        )
                    )

                    period_label = period_start.strftime(
                        "%m-%d" if interval_days == 1 else "%m-%d to"
                    )
                    if interval_days > 1:
                        period_label += " " + (period_end - timedelta(days=1)).strftime(
                            "%m-%d"
                        )

                    trends_table.add_row(
                        period_label,
                        str(new_users or 0),
                        str(new_docs or 0),
                        str(new_convs or 0),
                        str(messages or 0),
                        str(tokens or 0),
                    )

                console.print(trends_table)

                # Growth analysis
                if intervals >= 2:
                    # Compare first and last periods
                    first_period_end = start_date + timedelta(days=interval_days)
                    last_period_start = start_date + timedelta(
                        days=(intervals - 1) * interval_days
                    )

                    first_messages = await db.scalar(
                        select(func.count(Message.id)).where(
                            and_(
                                Message.created_at >= start_date,
                                Message.created_at < first_period_end,
                            )
                        )
                    )

                    last_messages = await db.scalar(
                        select(func.count(Message.id)).where(
                            Message.created_at >= last_period_start
                        )
                    )

                    if first_messages and last_messages:
                        growth_rate = (
                            (last_messages - first_messages) / first_messages
                        ) * 100
                        growth_status = (
                            "📈 Growing"
                            if growth_rate > 0
                            else "📉 Declining" if growth_rate < -10 else "➡️ Stable"
                        )

                        growth_panel = Panel(
                            f"Message Activity Growth: {growth_rate:+.1f}%\n{growth_status}",
                            title="📊 Growth Analysis",
                            border_style=(
                                "green"
                                if growth_rate > 0
                                else "red" if growth_rate < -10 else "yellow"
                            ),
                        )
                        console.print(growth_panel)

            except Exception as e:
                error_message(f"Failed to generate usage trends: {e}")

    _usage_trends()


@analytics_app.command()
def export_report(
    output_file: str = typer.Option(
        "analytics_report", "--output", "-o", help="Output file path"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json, csv (appended to path)"
    ),
    include_details: bool = typer.Option(
        False, "--details", "-d", help="Include detailed breakdowns"
    ),
):
    """Export comprehensive analytics report."""

    @async_command
    async def _export_report():
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.now()

                # Gather comprehensive analytics data
                report_data = {
                    "generated_at": now.isoformat(),
                    "system_overview": {},
                    "usage_statistics": {},
                    "performance_metrics": {},
                    "user_analytics": {},
                }

                # System overview
                total_users = await db.scalar(select(func.count(User.id)))
                total_docs = await db.scalar(select(func.count(Document.id)))
                total_convs = await db.scalar(select(func.count(Conversation.id)))
                total_messages = await db.scalar(select(func.count(Message.id)))

                report_data["system_overview"] = {
                    "total_users": total_users or 0,
                    "active_users": await db.scalar(
                        select(func.count(User.id)).where(User.is_active)
                    )
                    or 0,
                    "total_documents": total_docs or 0,
                    "completed_documents": await db.scalar(
                        select(func.count(Document.id)).where(
                            Document.status == FileStatus.COMPLETED
                        )
                    )
                    or 0,
                    "total_conversations": total_convs or 0,
                    "active_conversations": await db.scalar(
                        select(func.count(Conversation.id)).where(
                            Conversation.is_active
                        )
                    )
                    or 0,
                    "total_messages": total_messages or 0,
                    "total_storage_bytes": await db.scalar(
                        select(func.sum(Document.file_size))
                    )
                    or 0,
                    "total_tokens": await db.scalar(
                        select(func.sum(Message.token_count))
                    )
                    or 0,
                }

                # Export based on format

                if format == "json":
                    import json

                    output_path = Path(output_file + ".json")
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(
                            report_data, f, indent=2, ensure_ascii=False, default=str
                        )

                elif format == "csv":
                    import csv

                    output_path = Path(output_file + ".csv")
                    with open(output_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Metric", "Value"])
                        for category, metrics in report_data.items():
                            if isinstance(metrics, dict):
                                for metric, value in metrics.items():
                                    writer.writerow([f"{category}.{metric}", value])
                            else:
                                writer.writerow([category, metrics])

                else:
                    error_message(f"Unsupported format: {format}")
                    return

                success_message(f"Analytics report exported to: {output_path}")
                info_message(f"Format: {format}")

            except Exception as e:
                error_message(f"Failed to export analytics report: {e}")

    _export_report()
