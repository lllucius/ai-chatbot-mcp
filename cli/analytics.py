"""Analytics and reporting commands for the AI Chatbot Platform CLI.

This module provides comprehensive analytics and business intelligence functionality
through async operations and the AI Chatbot SDK for accessing platform metrics
and generating reports.
"""

from typing import Optional

from async_typer import AsyncTyper
from rich.console import Console
from typer import Option

from cli.base import error_message, get_sdk, success_message, ApiError

console = Console()

analytics_app = AsyncTyper(
    help="Analytics and reporting commands", rich_markup_mode=None
)


@analytics_app.async_command()
async def overview():
    """Show high-level analytics overview."""
    try:
        sdk = await get_sdk()
        data = await sdk.analytics.get_overview()
        if data:
            from rich.table import Table

            overview = data.get("data", data)
            table = Table(title="Analytics Overview")
            for k, v in overview.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        table.add_row(f"{k} - {subk}", str(subv))
                else:
                    table.add_row(k, str(v))
            console.print(table)
    except ApiError as e:
        error_message(f"Failed to get analytics overview: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get analytics overview: {str(e)}")


@analytics_app.async_command()
async def usage(
    period: Optional[str] = Option(
        None, "--period", help="Usage period: 1d, 7d, 30d, etc."
    ),
    detailed: bool = Option(False, "--detailed", help="Show detailed usage"),
):
    """Show usage analytics."""
    try:
        sdk = await get_sdk()
        data = await sdk.analytics.get_usage(period, detailed)
        if data:
            from rich.table import Table

            usage = data.get("usage", data)
            table = Table(title=f"Usage Analytics ({period or 'default'})")
            for k, v in usage.items():
                table.add_row(str(k), str(v))
            console.print(table)
    except ApiError as e:
        error_message(f"Failed to get usage analytics: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get usage analytics: {str(e)}")


@analytics_app.async_command()
async def performance():
    """Show system performance metrics."""
    try:
        sdk = await get_sdk()
        data = await sdk.analytics.get_performance()
        if data:
            from rich.table import Table

            perf = data.get("performance", data)
            table = Table(title="Performance Metrics")
            for k, v in perf.items():
                table.add_row(str(k), str(v))
            console.print(table)
    except ApiError as e:
        error_message(f"Failed to get performance metrics: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to get performance metrics: {str(e)}")


@analytics_app.async_command()
async def export_report(
    output: Optional[str] = Option(None, "--output", help="Export report output file"),
    details: bool = Option(False, "--details", help="Include detailed report"),
):
    """Export analytics report."""
    try:
        sdk = await get_sdk()
        data = await sdk.analytics.export_report(output=output, details=details)
        if getattr(data, "success", False) or data.get("success", False):
            success_message(
                f"Analytics report exported{' to ' + output if output else ''}."
            )
        else:
            error_message(getattr(data, "message", "Failed to export report"))
    except ApiError as e:
        error_message(f"Failed to export analytics report: {e.body['message']}")
    except Exception as e:
        error_message(f"Failed to export analytics report: {str(e)}")
