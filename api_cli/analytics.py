"""
Analytics commands for the API-based CLI.

This module provides analytics and reporting functionality through API calls.
"""

import typer
from .base import get_sdk_with_auth, console, error_message

analytics_app = typer.Typer(help="📊 Analytics and reporting commands")


@analytics_app.command()
def overview():
    """Show system overview and key metrics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.get_overview()
        
        if data:
            from rich.table import Table
            from rich.panel import Panel
            from rich.columns import Columns
            
            # Create overview panels
            users_data = data.get("users", {})
            docs_data = data.get("documents", {})
            convs_data = data.get("conversations", {})
            health_data = data.get("system_health", {})
            
            panels = []
            
            panels.append(Panel(
                f"Total: [green]{users_data.get('total', 0)}[/green]\n"
                f"Active: [blue]{users_data.get('active', 0)}[/blue]\n"
                f"Rate: [yellow]{users_data.get('activity_rate', 0):.1f}%[/yellow]",
                title="👥 Users",
                border_style="cyan"
            ))
            
            panels.append(Panel(
                f"Total: [green]{docs_data.get('total', 0)}[/green]\n"
                f"Processed: [blue]{docs_data.get('processed', 0)}[/blue]\n"
                f"Rate: [yellow]{docs_data.get('processing_rate', 0):.1f}%[/yellow]",
                title="📄 Documents",
                border_style="green"
            ))
            
            panels.append(Panel(
                f"Total: [green]{convs_data.get('total', 0)}[/green]",
                title="💬 Conversations",
                border_style="blue"
            ))
            
            panels.append(Panel(
                f"Score: [green]{health_data.get('score', 0)}/100[/green]",
                title="🏥 Health",
                border_style="yellow"
            ))
            
            console.print(Columns(panels))
    
    except Exception as e:
        error_message(f"Failed to get overview: {str(e)}")
        raise typer.Exit(1)


@analytics_app.command()
def usage(
    period: str = typer.Option("7d", "--period", help="Time period: 1d, 7d, 30d, 90d"),
    detailed: bool = typer.Option(False, "--detailed", help="Include detailed breakdown"),
):
    """Show usage statistics for the specified period."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.get_usage(period=period, detailed=detailed)
        
        if data:
            from rich.table import Table
            
            metrics = data.get("metrics", {})
            
            table = Table(title=f"Usage Statistics - {period}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("New Users", str(metrics.get("new_users", 0)))
            table.add_row("New Documents", str(metrics.get("new_documents", 0)))
            table.add_row("New Conversations", str(metrics.get("new_conversations", 0)))
            table.add_row("Total Messages", str(metrics.get("total_messages", 0)))
            table.add_row("Avg Messages/Day", str(metrics.get("avg_messages_per_day", 0)))
            
            console.print(table)
            
            if detailed and "daily_breakdown" in data:
                # Show daily breakdown
                daily_table = Table(title="Daily Breakdown")
                daily_table.add_column("Date", style="cyan")
                daily_table.add_column("Messages", style="green")
                
                for day_data in data["daily_breakdown"][-7:]:  # Last 7 days
                    daily_table.add_row(
                        day_data.get("date", ""),
                        str(day_data.get("messages", 0))
                    )
                
                console.print(daily_table)
    
    except Exception as e:
        error_message(f"Failed to get usage statistics: {str(e)}")
        raise typer.Exit(1)


@analytics_app.command()
def performance():
    """Show system performance metrics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.get_performance()
        
        if data:
            from rich.table import Table
            
            doc_perf = data.get("document_processing", {})
            
            table = Table(title="Performance Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Total Documents", str(doc_perf.get("total_documents", 0)))
            table.add_row("Completed", str(doc_perf.get("completed", 0)))
            table.add_row("Failed", str(doc_perf.get("failed", 0)))
            table.add_row("Processing", str(doc_perf.get("processing", 0)))
            table.add_row("Success Rate", f"{doc_perf.get('success_rate', 0):.1f}%")
            table.add_row("Failure Rate", f"{doc_perf.get('failure_rate', 0):.1f}%")
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to get performance metrics: {str(e)}")
        raise typer.Exit(1)


@analytics_app.command()
def users(
    metric: str = typer.Option("messages", "--metric", help="Metric: messages, documents, conversations"),
    top: int = typer.Option(10, "--top", help="Number of top users"),
    period: str = typer.Option("30d", "--period", help="Time period"),
):
    """Show user activity analytics."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.get_users_analytics(top=top, metric=metric)
        
        if data:
            from rich.table import Table
            
            top_users = data.get("top_users", [])
            
            table = Table(title=f"Top Users by {metric.title()}")
            table.add_column("Username", style="cyan")
            table.add_column("Email", style="blue")
            table.add_column("Count", style="green")
            
            for user in top_users:
                table.add_row(
                    user.get("username", ""),
                    user.get("email", ""),
                    str(user.get("count", 0))
                )
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to get user analytics: {str(e)}")
        raise typer.Exit(1)


@analytics_app.command()
def trends(
    days: int = typer.Option(14, "--days", help="Number of days to analyze"),
):
    """Show usage trends over time."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.get_trends()
        
        if data:
            from rich.table import Table
            
            summary = data.get("summary", {})
            
            table = Table(title=f"Trends Summary - {days} days")
            table.add_column("Metric", style="cyan")
            table.add_column("Total", style="white")
            
            table.add_row("New Users", str(summary.get("total_new_users", 0)))
            table.add_row("New Documents", str(summary.get("total_new_documents", 0)))
            table.add_row("Total Messages", str(summary.get("total_messages", 0)))
            table.add_row("Weekly Growth", f"{summary.get('weekly_growth_rate', 0):.1f}%")
            
            console.print(table)
    
    except Exception as e:
        error_message(f"Failed to get trends: {str(e)}")
        raise typer.Exit(1)


@analytics_app.command("export-report")
def export_report(
    include_details: bool = typer.Option(True, "--details/--no-details", help="Include detailed breakdowns"),
    output: str = typer.Option("report.json", "--output", "-o", help="Output file"),
):
    """Export comprehensive analytics report."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.analytics.export_report(output=output, details=include_details)
        
        if data:
            import json
            
            with open(output, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            from .base import success_message
            success_message(f"Analytics report exported to {output}")
    
    except Exception as e:
        error_message(f"Failed to export report: {str(e)}")
        raise typer.Exit(1)