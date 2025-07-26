"""
Task management commands for the API-based CLI.

This module provides background task management functionality through API calls.
"""

import typer

from .base import console, error_message, get_sdk_with_auth

tasks_app = typer.Typer(help="⚙️ Background task management commands")


@tasks_app.command()
def status():
    """Show background task system status."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.tasks.get_status()
        
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
        raise typer.Exit(1)


@tasks_app.command()
def workers():
    """Show information about Celery workers."""
    
    try:
        sdk = get_sdk_with_auth()
        
        data = sdk.tasks.get_workers()
        
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
                    str(worker.get("max_concurrency", 0))
                )
            
            console.print(table)
            
            summary = f"Total: {data.get('total_workers', 0)}, Online: {data.get('online_workers', 0)}"
            console.print(f"\n[dim]{summary}[/dim]")
    
    except Exception as e:
        error_message(f"Failed to get worker information: {str(e)}")
        raise typer.Exit(1)


@tasks_app.command()
def queue(
    queue_name: str = typer.Option(None, "--queue", help="Specific queue to check"),
):
    """Show task queue information."""
    
    async def _show_queue():
        client = get_client_with_auth()
        
        try:
            params = {}
            if queue_name:
                params["queue_name"] = queue_name
            
            response = await client.get("/api/v1/tasks/queue", params=params)
            data = handle_api_response(response, "getting queue information")
            
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
                    total_tasks = queue.get("active", 0) + queue.get("reserved", 0) + queue.get("scheduled", 0)
                    table.add_row(
                        queue.get("name", ""),
                        str(queue.get("active", 0)),
                        str(queue.get("reserved", 0)),
                        str(queue.get("scheduled", 0)),
                        str(total_tasks)
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get queue information: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_queue())


@tasks_app.command()
def active():
    """Show currently active tasks."""
    
    async def _show_active():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/tasks/active")
            data = handle_api_response(response, "getting active tasks")
            
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
                        task.get("id", "")[:8] + "...",  # Truncate ID
                        task.get("name", ""),
                        task.get("worker", ""),
                        task.get("time_start", "")
                    )
                
                console.print(table)
        
        except Exception as e:
            error_message(f"Failed to get active tasks: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_active())


@tasks_app.command()
def schedule(
    task_name: str = typer.Argument(..., help="Name of the task to schedule"),
    args: str = typer.Option("[]", "--args", help="JSON array of task arguments"),
    kwargs: str = typer.Option("{}", "--kwargs", help="JSON object of task keyword arguments"),
    countdown: int = typer.Option(None, "--countdown", help="Delay in seconds"),
    queue: str = typer.Option("default", "--queue", help="Queue to send the task to"),
):
    """Schedule a background task for execution."""
    
    async def _schedule_task():
        client = get_client_with_auth()
        
        try:
            params = {
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs,
                "queue": queue
            }
            
            if countdown is not None:
                params["countdown"] = countdown
            
            response = await client.post("/api/v1/tasks/schedule", params=params)
            data = handle_api_response(response, "scheduling task")
            
            if data:
                from rich.panel import Panel
                
                task_panel = Panel(
                    f"Task: [green]{data.get('task_id', '')}[/green]\n"
                    f"Queue: [blue]{data.get('queue', '')}[/blue]\n"
                    f"Countdown: [yellow]{data.get('countdown', 'None')} seconds[/yellow]",
                    title=f"Task Scheduled: {task_name}",
                    border_style="green"
                )
                console.print(task_panel)
        
        except Exception as e:
            error_message(f"Failed to schedule task: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_schedule_task())


@tasks_app.command("retry-failed")
def retry_failed(
    task_name: str = typer.Option(None, "--task", help="Specific task name to retry"),
    max_retries: int = typer.Option(10, "--max", help="Maximum number of tasks to retry"),
):
    """Retry failed document processing tasks."""
    
    async def _retry_failed():
        client = get_client_with_auth()
        
        try:
            params = {"max_retries": max_retries}
            if task_name:
                params["task_name"] = task_name
            
            response = await client.post("/api/v1/tasks/retry-failed", params=params)
            data = handle_api_response(response, "retrying failed tasks")
            
            if data:
                from rich.panel import Panel
                
                retry_panel = Panel(
                    f"Retried: [green]{data.get('retried_count', 0)}[/green]\n"
                    f"Total Failed: [yellow]{data.get('total_failed', 0)}[/yellow]\n"
                    f"Errors: [red]{len(data.get('errors', []))}[/red]",
                    title="Retry Results",
                    border_style="blue"
                )
                console.print(retry_panel)
                
                # Show errors if any
                errors = data.get("errors", [])
                if errors:
                    console.print("\n[bold]Errors:[/bold]")
                    for error in errors:
                        console.print(f"• {error}")
        
        except Exception as e:
            error_message(f"Failed to retry tasks: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_retry_failed())


@tasks_app.command()
def purge(
    queue_name: str = typer.Option("default", "--queue", help="Queue name to purge"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Purge all tasks from a queue."""
    
    async def _purge_queue():
        from .base import confirm_action
        
        if not force:
            if not confirm_action(f"Are you sure you want to purge all tasks from queue '{queue_name}'?"):
                return
        
        client = get_client_with_auth()
        
        try:
            params = {"queue_name": queue_name}
            response = await client.post("/api/v1/tasks/purge", params=params)
            handle_api_response(response, "purging queue")
        
        except Exception as e:
            error_message(f"Failed to purge queue: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_purge_queue())


@tasks_app.command()
def stats(
    period_hours: int = typer.Option(24, "--period", help="Period in hours for statistics"),
):
    """Show task execution statistics."""
    
    async def _show_stats():
        client = get_client_with_auth()
        
        try:
            params = {"period_hours": period_hours}
            response = await client.get("/api/v1/tasks/stats", params=params)
            data = handle_api_response(response, "getting task statistics")
            
            if data:
                from rich.panel import Panel
                
                doc_processing = data.get("document_processing", {})
                
                # Processing stats
                stats_panel = Panel(
                    f"Total: [white]{doc_processing.get('total', 0)}[/white]\n"
                    f"Completed: [green]{doc_processing.get('completed', 0)}[/green]\n"
                    f"Failed: [red]{doc_processing.get('failed', 0)}[/red]\n"
                    f"Processing: [yellow]{doc_processing.get('processing', 0)}[/yellow]\n"
                    f"Success Rate: [blue]{doc_processing.get('success_rate', 0):.1f}%[/blue]\n"
                    f"Avg Time: [cyan]{doc_processing.get('avg_processing_time_seconds', 0):.1f}s[/cyan]",
                    title=f"Document Processing ({period_hours}h)",
                    border_style="blue"
                )
                console.print(stats_panel)
                
                # Recent errors
                recent_errors = data.get("recent_errors", [])
                if recent_errors:
                    console.print("\n[bold]Recent Errors (Sample):[/bold]")
                    for i, error in enumerate(recent_errors[:3], 1):
                        console.print(f"{i}. {error}")
        
        except Exception as e:
            error_message(f"Failed to get task statistics: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_show_stats())


@tasks_app.command()
def monitor():
    """Get real-time monitoring data for task system."""
    
    async def _monitor_tasks():
        client = get_client_with_auth()
        
        try:
            response = await client.get("/api/v1/tasks/monitor")
            data = handle_api_response(response, "getting monitoring data")
            
            if data:
                from rich.columns import Columns
                from rich.panel import Panel
                
                system_status = data.get("system_status", {})
                active_tasks = data.get("active_tasks", {})
                workers = data.get("workers", {})
                
                # Create monitoring panels
                panels = []
                
                panels.append(Panel(
                    f"Status: [green]{system_status.get('broker_status', 'Unknown')}[/green]\n"
                    f"Workers: [blue]{system_status.get('active_workers', 0)}[/blue]\n"
                    f"Tasks: [yellow]{system_status.get('active_tasks', 0)}[/yellow]",
                    title="System",
                    border_style="cyan"
                ))
                
                panels.append(Panel(
                    f"Active: [green]{active_tasks.get('count', 0)}[/green]\n"
                    f"Workers Busy: [yellow]{active_tasks.get('workers_busy', 0)}[/yellow]",
                    title="Tasks",
                    border_style="green"
                ))
                
                panels.append(Panel(
                    f"Total: [blue]{workers.get('total', 0)}[/blue]\n"
                    f"Online: [green]{workers.get('online', 0)}[/green]",
                    title="Workers",
                    border_style="blue"
                ))
                
                console.print(Columns(panels))
                
                # Performance data
                recent_perf = data.get("recent_performance", {})
                if recent_perf:
                    perf_panel = Panel(
                        f"Success Rate: [green]{recent_perf.get('success_rate', 0):.1f}%[/green]\n"
                        f"Avg Processing: [blue]{recent_perf.get('avg_processing_time_seconds', 0):.1f}s[/blue]",
                        title="Recent Performance",
                        border_style="yellow"
                    )
                    console.print(perf_panel)
                
                refresh_interval = data.get("refresh_interval", 30)
                console.print(f"\n[dim]Suggested refresh interval: {refresh_interval} seconds[/dim]")
        
        except Exception as e:
            error_message(f"Failed to get monitoring data: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_monitor_tasks())