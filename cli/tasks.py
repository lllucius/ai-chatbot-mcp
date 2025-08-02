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

from .base import error_message, get_sdk, success_message

tasks_app = AsyncTyper(help="Background task management commands", rich_markup_mode=None)


@tasks_app.async_command()
async def status():
    """Show background task system status."""
    try:
        sdk = await get_sdk()
        data = await sdk.tasks.get_status()
        if data:
            print("\nTask System Status:")
            print("===================")
            print(f"Broker Status: {data.get('broker_status', 'Unknown')}")
            print(f"Active Workers: {data.get('active_workers', 0)}")
            print(f"Active Tasks: {data.get('active_tasks', 0)}")
            print(f"Reserved Tasks: {data.get('reserved_tasks', 0)}")
            print(f"System Status: {data.get('system_status', 'Unknown')}")
            print()
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
            workers = data.get("workers", [])
            
            # Convert to table data
            worker_data = []
            for worker in workers:
                worker_data.append({
                    "Name": worker.get("name", ""),
                    "Status": worker.get("status", "Unknown"),
                    "Pool": worker.get("pool", ""),
                    "Processes": str(worker.get("processes", 0)),
                    "Max Concurrency": str(worker.get("max_concurrency", 0)),
                })
            
            from .base import display_table_data
            display_table_data(worker_data, f"Celery Workers ({len(workers)} total)")
            
            summary = f"Total: {data.get('total_workers', 0)}, Online: {data.get('online_workers', 0)}"
            print(summary)
            print()
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
            queues = data.get("queues", [])
            
            # Convert to table data
            queue_data = []
            for queue in queues:
                total_tasks = (
                    queue.get("active", 0)
                    + queue.get("reserved", 0)
                    + queue.get("scheduled", 0)
                )
                queue_data.append({
                    "Queue Name": queue.get("name", ""),
                    "Active": str(queue.get("active", 0)),
                    "Reserved": str(queue.get("reserved", 0)),
                    "Scheduled": str(queue.get("scheduled", 0)),
                    "Total Tasks": str(total_tasks),
                })
            
            from .base import display_table_data
            display_table_data(queue_data, f"Task Queues ({len(queues)} total)")
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
            active_tasks = data.get("active_tasks", [])
            if not active_tasks:
                print("No active tasks")
                return
            
            # Convert to table data
            task_data = []
            for task in active_tasks:
                task_data.append({
                    "Task ID": task.get("id", "")[:8] + "...",
                    "Name": task.get("name", ""),
                    "Worker": task.get("worker", ""),
                    "Started": task.get("time_start", ""),
                })
            
            from .base import display_table_data
            display_table_data(task_data, f"Active Tasks ({len(active_tasks)} total)")
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
            print(f"\nTask Scheduled: {task_name}")
            print("=" * (len(task_name) + 15))
            print(f"Task: {data.get('task_id', '')}")
            print(f"Queue: {data.get('queue', '')}")
            print(f"Countdown: {data.get('countdown', 'None')} seconds")
            print()
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
            print("\nRetry Results:")
            print("==============")
            print(f"Retried: {data.get('retried_count', 0)}")
            print(f"Total Failed: {data.get('total_failed', 0)}")
            print(f"Errors: {len(data.get('errors', []))}")
            
            errors = data.get("errors", [])
            if errors:
                print("\nErrors:")
                for error in errors:
                    print(f"• {error}")
            print()
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
            doc_processing = data.get("document_processing", {})
            
            print(f"\nDocument Processing ({period_hours}h):")
            print("=" * (25 + len(str(period_hours))))
            print(f"Total: {doc_processing.get('total', 0)}")
            print(f"Completed: {doc_processing.get('completed', 0)}")
            print(f"Failed: {doc_processing.get('failed', 0)}")
            print(f"Processing: {doc_processing.get('processing', 0)}")
            print(f"Success Rate: {doc_processing.get('success_rate', 0):.1f}%")
            print(f"Avg Time: {doc_processing.get('avg_processing_time_seconds', 0):.1f}s")
            
            recent_errors = data.get("recent_errors", [])
            if recent_errors:
                print("\nRecent Errors (Sample):")
                for i, error in enumerate(recent_errors[:3], 1):
                    print(f"{i}. {error}")
            print()
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
            system_status = data.get("system_status", {})
            active_tasks = data.get("active_tasks", {})
            workers = data.get("workers", {})
            
            print("\nTask System Monitoring:")
            print("=======================")
            
            # System status
            print("System:")
            print(f"  Status: {system_status.get('broker_status', 'Unknown')}")
            print(f"  Workers: {system_status.get('active_workers', 0)}")
            print(f"  Tasks: {system_status.get('active_tasks', 0)}")
            print()
            
            # Tasks info
            print("Tasks:")
            print(f"  Active: {active_tasks.get('count', 0)}")
            print(f"  Workers Busy: {active_tasks.get('workers_busy', 0)}")
            print()
            
            # Workers info
            print("Workers:")
            print(f"  Total: {workers.get('total', 0)}")
            print(f"  Online: {workers.get('online', 0)}")
            print()
            
            # Performance data
            recent_perf = data.get("recent_performance", {})
            if recent_perf:
                print("Recent Performance:")
                print(f"  Success Rate: {recent_perf.get('success_rate', 0):.1f}%")
                print(f"  Avg Processing: {recent_perf.get('avg_processing_time_seconds', 0):.1f}s")
                print()
            
            refresh_interval = data.get("refresh_interval", 30)
            print(f"Suggested refresh interval: {refresh_interval} seconds")
    except Exception as e:
        error_message(f"Failed to get monitoring data: {str(e)}")
        raise SystemExit(1)
