"""
Background task management commands for the AI Chatbot Platform CLI.

This module provides comprehensive management of background tasks and job queues
through async operations and the AI Chatbot SDK. It enables administrators and
developers to monitor, control, and optimize background processing systems
including Celery workers and task queues.

Background tasks handle asynchronous operations such as document processing,
email notifications, data exports, and other long-running operations that
should not block the main application. This module provides tools for managing
these tasks effectively in production environments.

Key Features:
    - Task queue monitoring and status reporting
    - Worker management and scaling operations
    - Task scheduling and cron job management
    - Performance monitoring and optimization
    - Error tracking and retry management
    - Resource utilization and capacity planning

Queue Management:
    - Real-time queue status and backlog monitoring
    - Task prioritization and scheduling
    - Dead letter queue management
    - Queue cleanup and maintenance operations
    - Performance metrics and throughput analysis

Worker Operations:
    - Worker status monitoring and health checks
    - Dynamic worker scaling and load balancing
    - Worker restart and recovery operations
    - Resource utilization tracking
    - Error rate monitoring and alerting

Task Lifecycle:
    - Task creation and submission
    - Progress tracking and status updates
    - Result retrieval and processing
    - Error handling and retry mechanisms
    - Task cancellation and cleanup

Performance Monitoring:
    - Task execution time analysis
    - Queue throughput and latency metrics
    - Worker efficiency and utilization rates
    - Error rate tracking and alerting
    - Capacity planning and resource optimization

Use Cases:
    - Document processing and analysis pipelines
    - Bulk email and notification systems
    - Data export and report generation
    - Machine learning model training
    - System maintenance and cleanup tasks

Example Usage:
    ```bash
    # System monitoring
    ai-chatbot tasks status --detailed
    ai-chatbot tasks workers --show-inactive
    ai-chatbot tasks queues --include-metrics

    # Task management
    ai-chatbot tasks list --status running --limit 20
    ai-chatbot tasks show task_id --include-logs
    ai-chatbot tasks cancel task_id --force

    # Performance and optimization
    ai-chatbot tasks performance --period week
    ai-chatbot tasks cleanup --older-than 30d
    ai-chatbot tasks scale-workers --queue default --count 5
    ```
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from .base import console, error_message, get_sdk, success_message

tasks_app = AsyncTyper(help="⚙️ Background task management commands")


@tasks_app.async_command()
async def status():
    """Show background task system status."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.get_status()
        if data:
            from rich.table import Table

            table = Table(title="Task System Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("Broker Status", data.get("broker_status", "Unknown"))
            table.add_row("Active Workers", str(data.get("active_workers", 0)))
            table.add_row("Active Tasks", str(data.get("active_tasks", 0)))
            table.add_row("Reserved Tasks", str(data.get("reserved_tasks", 0)))
            table.add_row("System Status", data.get("system_status", "Unknown"))
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get task status: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def workers():
    """Show information about Celery workers."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.get_workers()
        if data:
            from rich.table import Table

            workers = data.get("workers", [])
            table = Table(title=f"Celery Workers ({len(workers)} total)")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Pool", style="blue")
            table.add_column("Processes", style="green")
            table.add_column("Max Concurrency", style="yellow")
            for worker in workers:
                status_color = "green" if worker.get("status") == "online" else "red"
                table.add_row(
                    worker.get("name", ""),
                    f"[{status_color}]{worker.get('status', 'Unknown')}[/{status_color}]",
                    worker.get("pool", ""),
                    str(worker.get("processes", 0)),
                    str(worker.get("max_concurrency", 0)),
                )
            console.print(table)
            summary = f"Total: {data.get('total_workers', 0)}, Online: {data.get('online_workers', 0)}"
            console.print(f"\n[dim]{summary}[/dim]")
    except Exception as e:
        error_message(f"Failed to get worker information: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def queue(
    queue_name: Optional[str] = Option(None, "--queue", help="Specific queue to check"),
):
    """Show task queue information."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.get_queue()
        if data:
            from rich.table import Table

            queues = data.get("queues", [])
            table = Table(title=f"Task Queues ({len(queues)} total)")
            table.add_column("Queue Name", style="cyan")
            table.add_column("Active", style="green")
            table.add_column("Reserved", style="yellow")
            table.add_column("Scheduled", style="blue")
            table.add_column("Total Tasks", style="white")
            for queue in queues:
                total_tasks = (
                    queue.get("active", 0)
                    + queue.get("reserved", 0)
                    + queue.get("scheduled", 0)
                )
                table.add_row(
                    queue.get("name", ""),
                    str(queue.get("active", 0)),
                    str(queue.get("reserved", 0)),
                    str(queue.get("scheduled", 0)),
                    str(total_tasks),
                )
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get queue information: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def active():
    """Show currently active tasks."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.get_active()
        if data:
            from rich.table import Table

            active_tasks = data.get("active_tasks", [])
            if not active_tasks:
                console.print("[green]No active tasks[/green]")
                return
            table = Table(title=f"Active Tasks ({len(active_tasks)} total)")
            table.add_column("Task ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Worker", style="blue")
            table.add_column("Started", style="yellow")
            for task in active_tasks:
                table.add_row(
                    task.get("id", "")[:8] + "...",
                    task.get("name", ""),
                    task.get("worker", ""),
                    task.get("time_start", ""),
                )
            console.print(table)
    except Exception as e:
        error_message(f"Failed to get active tasks: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def schedule(
    task_name: str = Argument(..., help="Name of the task to schedule"),
    args: str = Option("[]", "--args", help="JSON array of task arguments"),
    kwargs: str = Option(
        "{}", "--kwargs", help="JSON object of task keyword arguments"
    ),
    countdown: Optional[int] = Option(None, "--countdown", help="Delay in seconds"),
    queue: str = Option("default", "--queue", help="Queue to send the task to"),
):
    """Schedule a background task for execution."""
    try:
        sdk = await get_sdk()
        params = {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "queue": queue,
        }
        if countdown is not None:
            params["countdown"] = countdown
        data = await sdk.tasks.schedule_task(**params)
        if data:
            from rich.panel import Panel

            task_panel = Panel(
                f"Task: [green]{data.get('task_id', '')}[/green]\n"
                f"Queue: [blue]{data.get('queue', '')}[/blue]\n"
                f"Countdown: [yellow]{data.get('countdown', 'None')} seconds[/yellow]",
                title=f"Task Scheduled: {task_name}",
                border_style="green",
            )
            console.print(task_panel)
    except Exception as e:
        error_message(f"Failed to schedule task: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command("retry-failed")
async def retry_failed(
    task_name: Optional[str] = Option(
        None, "--task", help="Specific task name to retry"
    ),
    max_retries: int = Option(10, "--max", help="Maximum number of tasks to retry"),
):
    """Retry failed document processing tasks."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.retry_failed()
        if data:
            from rich.panel import Panel

            retry_panel = Panel(
                f"Retried: [green]{data.get('retried_count', 0)}[/green]\n"
                f"Total Failed: [yellow]{data.get('total_failed', 0)}[/yellow]\n"
                f"Errors: [red]{len(data.get('errors', []))}[/red]",
                title="Retry Results",
                border_style="blue",
            )
            console.print(retry_panel)
            errors = data.get("errors", [])
            if errors:
                console.print("\n[bold]Errors:[/bold]")
                for error in errors:
                    console.print(f"• {error}")
    except Exception as e:
        error_message(f"Failed to retry tasks: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def purge(
    queue_name: str = Option("default", "--queue", help="Queue name to purge"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Purge all tasks from a queue."""
    from .base import confirm_action

    if not force and not confirm_action(
        f"Are you sure you want to purge all tasks from queue '{queue_name}'?"
    ):
        return
    try:
        sdk = await get_sdk()
        await sdk.tasks.purge_queue()
        success_message(f"Purged queue '{queue_name}'.")
    except Exception as e:
        error_message(f"Failed to purge queue: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def stats(
    period_hours: int = Option(24, "--period", help="Period in hours for statistics"),
):
    """Show task execution statistics."""
    try:
        sdk = await get_sdk()
        # Let's assume get_stats returns a summary and recent_errors
        data = await sdk.tasks.monitor(refresh=None, duration=period_hours)
        if data:
            from rich.panel import Panel

            doc_processing = data.get("document_processing", {})
            stats_panel = Panel(
                f"Total: [white]{doc_processing.get('total', 0)}[/white]\n"
                f"Completed: [green]{doc_processing.get('completed', 0)}[/green]\n"
                f"Failed: [red]{doc_processing.get('failed', 0)}[/red]\n"
                f"Processing: [yellow]{doc_processing.get('processing', 0)}[/yellow]\n"
                f"Success Rate: [blue]{doc_processing.get('success_rate', 0):.1f}%[/blue]\n"
                f"Avg Time: [cyan]{doc_processing.get('avg_processing_time_seconds', 0):.1f}s[/cyan]",
                title=f"Document Processing ({period_hours}h)",
                border_style="blue",
            )
            console.print(stats_panel)
            recent_errors = data.get("recent_errors", [])
            if recent_errors:
                console.print("\n[bold]Recent Errors (Sample):[/bold]")
                for i, error in enumerate(recent_errors[:3], 1):
                    console.print(f"{i}. {error}")
    except Exception as e:
        error_message(f"Failed to get task statistics: {str(e)}")
        raise SystemExit(1)


@tasks_app.async_command()
async def monitor():
    """Get real-time monitoring data for task system."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.monitor()
        if data:
            from rich.columns import Columns
            from rich.panel import Panel

            system_status = data.get("system_status", {})
            active_tasks = data.get("active_tasks", {})
            workers = data.get("workers", {})
            panels = []
            panels.append(
                Panel(
                    f"Status: [green]{system_status.get('broker_status', 'Unknown')}[/green]\n"
                    f"Workers: [blue]{system_status.get('active_workers', 0)}[/blue]\n"
                    f"Tasks: [yellow]{system_status.get('active_tasks', 0)}[/yellow]",
                    title="System",
                    border_style="cyan",
                )
            )
            panels.append(
                Panel(
                    f"Active: [green]{active_tasks.get('count', 0)}[/green]\n"
                    f"Workers Busy: [yellow]{active_tasks.get('workers_busy', 0)}[/yellow]",
                    title="Tasks",
                    border_style="green",
                )
            )
            panels.append(
                Panel(
                    f"Total: [blue]{workers.get('total', 0)}[/blue]\n"
                    f"Online: [green]{workers.get('online', 0)}[/green]",
                    title="Workers",
                    border_style="blue",
                )
            )
            console.print(Columns(panels))
            recent_perf = data.get("recent_performance", {})
            if recent_perf:
                perf_panel = Panel(
                    f"Success Rate: [green]{recent_perf.get('success_rate', 0):.1f}%[/green]\n"
                    f"Avg Processing: [blue]{recent_perf.get('avg_processing_time_seconds', 0):.1f}s[/blue]",
                    title="Recent Performance",
                    border_style="yellow",
                )
                console.print(perf_panel)
            refresh_interval = data.get("refresh_interval", 30)
            console.print(
                f"\n[dim]Suggested refresh interval: {refresh_interval} seconds[/dim]"
            )
    except Exception as e:
        error_message(f"Failed to get monitoring data: {str(e)}")
        raise SystemExit(1)
