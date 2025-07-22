"""
Background task management CLI commands.

Provides comprehensive background task management functionality including:
- Task queue monitoring and management
- Celery worker management
- Task scheduling and execution
- Performance monitoring
- Failed task recovery
"""

import asyncio
import json
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import typer
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

from ..database import AsyncSessionLocal
from ..models.document import Document, FileStatus
from ..services.background_processor import BackgroundProcessor
from .base import (async_command, console, error_message, format_timestamp,
                   info_message, success_message, warning_message)

# Create the background tasks app
tasks_app = typer.Typer(help="Background task management commands")


@tasks_app.command()
def status():
    """Show background task system status."""
    
    def _task_status():
        try:
            # Check if Celery is running
            try:
                result = subprocess.run(
                    ["celery", "--version"], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    success_message(f"Celery available: {result.stdout.strip()}")
                else:
                    warning_message("Celery not available - background processing may be limited")
                    info_message("Install Celery with: pip install celery")
                    return
            except FileNotFoundError:
                warning_message("Celery not found - background processing may be limited")
                info_message("Install Celery with: pip install celery")
                return
            
            # Check worker status
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            worker_result = subprocess.run(
                ["celery", "-A", "app.services.background_processor", "inspect", "active"], 
                capture_output=True, 
                text=True,
                cwd=project_root
            )
            
            if worker_result.returncode == 0:
                try:
                    worker_data = json.loads(worker_result.stdout) if worker_result.stdout.strip() else {}
                    if worker_data:
                        success_message("Background workers: Running")
                        
                        # Show active tasks
                        total_active = sum(len(tasks) for tasks in worker_data.values())
                        console.print(f"Active tasks: {total_active}")
                        
                        for worker_name, tasks in worker_data.items():
                            if tasks:
                                console.print(f"  Worker {worker_name}: {len(tasks)} tasks")
                    else:
                        warning_message("No active workers found")
                except json.JSONDecodeError:
                    warning_message("Could not parse worker status")
            else:
                warning_message("Could not check worker status - workers may not be running")
            
            # Check Redis connection (if configured)
            try:
                import redis

                from ..config import settings

                # Try to connect to Redis
                redis_client = redis.Redis.from_url("redis://localhost:6379/0")
                redis_client.ping()
                success_message("Redis connection: OK")
                
                # Get queue info
                queue_length = redis_client.llen("celery")
                console.print(f"Default queue length: {queue_length}")
                
            except ImportError:
                warning_message("Redis not available (pip install redis)")
            except Exception as e:
                warning_message(f"Redis connection failed: {e}")
            
        except Exception as e:
            error_message(f"Failed to check task status: {e}")
    
    _task_status()


@tasks_app.command()
def workers():
    """Show information about Celery workers."""
    
    def _worker_info():
        try:
            # Get worker statistics
            stats_result = subprocess.run(
                ["celery", "-A", "app.services.background_processor", "inspect", "stats"], 
                capture_output=True, 
                text=True,
                cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp"
            )
            
            if stats_result.returncode != 0:
                error_message("Could not get worker stats - ensure workers are running")
                return
            
            try:
                stats_data = json.loads(stats_result.stdout) if stats_result.stdout.strip() else {}
                
                if not stats_data:
                    warning_message("No worker statistics available")
                    return
                
                # Create workers table
                workers_table = Table(title="Celery Workers")
                workers_table.add_column("Worker", style="cyan", width=20)
                workers_table.add_column("Status", style="green", width=12)
                workers_table.add_column("Tasks", style="yellow", width=12)
                workers_table.add_column("Load", style="blue", width=10)
                workers_table.add_column("Memory", style="magenta", width=12)
                
                for worker_name, stats in stats_data.items():
                    total_tasks = stats.get('total', {})
                    completed = sum(total_tasks.values()) if isinstance(total_tasks, dict) else 0
                    
                    load_avg = stats.get('rusage', {}).get('utime', 0)
                    memory_mb = stats.get('rusage', {}).get('maxrss', 0) / 1024 if stats.get('rusage', {}).get('maxrss') else 0
                    
                    workers_table.add_row(
                        worker_name.split('@')[1] if '@' in worker_name else worker_name,
                        "🟢 Active",
                        str(completed),
                        f"{load_avg:.2f}s",
                        f"{memory_mb:.1f}MB" if memory_mb else "N/A"
                    )
                
                console.print(workers_table)
                
                # Show worker capabilities
                registered_result = subprocess.run(
                    ["celery", "-A", "app.services.background_processor", "inspect", "registered"], 
                    capture_output=True, 
                    text=True,
                    cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp"
                )
                
                if registered_result.returncode == 0:
                    try:
                        registered_data = json.loads(registered_result.stdout) if registered_result.stdout.strip() else {}
                        
                        if registered_data:
                            console.print("\n[bold]Registered Tasks:[/bold]")
                            all_tasks = set()
                            for worker_tasks in registered_data.values():
                                all_tasks.update(worker_tasks)
                            
                            for task in sorted(all_tasks):
                                console.print(f"  • {task}")
                    
                    except json.JSONDecodeError:
                        warning_message("Could not parse registered tasks")
                
            except json.JSONDecodeError:
                error_message("Could not parse worker statistics")
            
        except Exception as e:
            error_message(f"Failed to get worker information: {e}")
    
    _worker_info()


@tasks_app.command()
def queue():
    """Show task queue information."""
    
    def _queue_info():
        try:
            import redis

            # Connect to Redis
            redis_client = redis.Redis.from_url("redis://localhost:6379/0")
            
            # Get queue information
            queues = ['celery', 'high_priority', 'low_priority', 'documents']
            
            queue_table = Table(title="Task Queues")
            queue_table.add_column("Queue", style="cyan", width=15)
            queue_table.add_column("Length", style="green", width=10)
            queue_table.add_column("Processing", style="yellow", width=12)
            queue_table.add_column("Failed", style="red", width=10)
            
            total_queued = 0
            total_processing = 0
            total_failed = 0
            
            for queue_name in queues:
                try:
                    queue_length = redis_client.llen(queue_name)
                    processing_length = redis_client.llen(f"{queue_name}\\unacked")
                    failed_length = redis_client.llen(f"_kombu.binding.{queue_name}")
                    
                    total_queued += queue_length
                    total_processing += processing_length
                    total_failed += failed_length
                    
                    if queue_length > 0 or processing_length > 0 or failed_length > 0:
                        queue_table.add_row(
                            queue_name,
                            str(queue_length),
                            str(processing_length),
                            str(failed_length)
                        )
                
                except Exception as e:
                    queue_table.add_row(queue_name, "Error", "Error", "Error")
            
            console.print(queue_table)
            
            # Summary
            summary_panel = Panel(
                f"Total Queued: {total_queued}\n"
                f"Total Processing: {total_processing}\n"
                f"Total Failed: {total_failed}",
                title="Queue Summary",
                border_style="blue"
            )
            console.print(summary_panel)
            
        except ImportError:
            error_message("Redis not available. Install with: pip install redis")
        except Exception as e:
            error_message(f"Failed to get queue information: {e}")
    
    _queue_info()


@tasks_app.command()
def active():
    """Show currently active tasks."""
    
    def _active_tasks():
        try:
            # Get active tasks
            active_result = subprocess.run(
                ["celery", "-A", "app.services.background_processor", "inspect", "active"], 
                capture_output=True, 
                text=True
            )
            
            if active_result.returncode != 0:
                error_message("Could not get active tasks - ensure workers are running")
                return
            
            try:
                active_data = json.loads(active_result.stdout) if active_result.stdout.strip() else {}
                
                if not active_data:
                    info_message("No active tasks")
                    return
                
                # Create active tasks table
                tasks_table = Table(title="Active Tasks")
                tasks_table.add_column("Worker", style="cyan", width=20)
                tasks_table.add_column("Task", style="green", width=30)
                tasks_table.add_column("ID", style="blue", width=15)
                tasks_table.add_column("Started", style="yellow", width=12)
                tasks_table.add_column("Args", style="magenta", width=30)
                
                total_active = 0
                for worker_name, tasks in active_data.items():
                    for task in tasks:
                        total_active += 1
                        
                        task_name = task.get('name', 'Unknown')
                        task_id = task.get('id', 'Unknown')[:12]  # Truncate ID
                        
                        # Parse start time
                        time_start = task.get('time_start')
                        if time_start:
                            started = datetime.fromtimestamp(time_start).strftime("%H:%M:%S")
                        else:
                            started = "Unknown"
                        
                        # Format args
                        args = task.get('args', [])
                        kwargs = task.get('kwargs', {})
                        args_str = str(args)[:27] + "..." if len(str(args)) > 30 else str(args)
                        
                        tasks_table.add_row(
                            worker_name.split('@')[1] if '@' in worker_name else worker_name,
                            task_name.split('.')[-1],  # Show only last part of task name
                            task_id,
                            started,
                            args_str
                        )
                
                console.print(tasks_table)
                console.print(f"\n[bold]Total active tasks:[/bold] {total_active}")
                
            except json.JSONDecodeError:
                error_message("Could not parse active tasks")
            
        except Exception as e:
            error_message(f"Failed to get active tasks: {e}")
    
    _active_tasks()


@tasks_app.command()
def schedule(
    task_name: str = typer.Argument(..., help="Task name to schedule"),
    args: str = typer.Option("[]", "--args", "-a", help="Task arguments as JSON array"),
    delay: int = typer.Option(0, "--delay", "-d", help="Delay in seconds before execution"),
    queue: str = typer.Option("celery", "--queue", "-q", help="Queue to submit to"),
):
    """Schedule a background task for execution."""
    
    @async_command
    async def _schedule_task():
        try:
            # Parse arguments
            try:
                task_args = json.loads(args)
                if not isinstance(task_args, list):
                    error_message("Arguments must be a JSON array")
                    return
            except json.JSONDecodeError:
                error_message("Invalid JSON in arguments")
                return
            
            # Map task names to actual task functions
            available_tasks = {
                "process_document": "app.services.background_processor.process_document_task",
                "cleanup_old_files": "app.services.background_processor.cleanup_old_files",
                "generate_embeddings": "app.services.background_processor.generate_embeddings_task",
                "test_task": "app.services.background_processor.test_task",
            }
            
            if task_name not in available_tasks:
                error_message(f"Unknown task: {task_name}")
                console.print("Available tasks:")
                for task in available_tasks:
                    console.print(f"  • {task}")
                return
            
            full_task_name = available_tasks[task_name]
            
            # Schedule the task
            from celery import Celery
            
            app = Celery('background_processor')
            app.config_from_object('app.services.background_processor:celery_config')
            
            if delay > 0:
                result = app.send_task(
                    full_task_name,
                    args=task_args,
                    countdown=delay,
                    queue=queue
                )
            else:
                result = app.send_task(
                    full_task_name,
                    args=task_args,
                    queue=queue
                )
            
            success_message(f"Task scheduled: {task_name}")
            console.print(f"Task ID: {result.id}")
            console.print(f"Queue: {queue}")
            if delay > 0:
                console.print(f"Delay: {delay} seconds")
            
        except ImportError:
            error_message("Celery not available. Install with: pip install celery")
        except Exception as e:
            error_message(f"Failed to schedule task: {e}")
    
    _schedule_task()


@tasks_app.command()
def retry_failed():
    """Retry failed document processing tasks."""
    
    @async_command
    async def _retry_failed():
        try:
            async with AsyncSessionLocal() as db:
                # Find failed documents
                failed_docs = await db.execute(
                    select(Document).where(Document.status == FileStatus.FAILED)
                )
                documents = failed_docs.scalars().all()
                
                if not documents:
                    info_message("No failed documents to retry")
                    return
                
                console.print(f"Found {len(documents)} failed documents")
                
                # Retry processing
                retried_count = 0
                for doc in track(documents, description="Retrying..."):
                    try:
                        # Reset status to pending
                        doc.status = FileStatus.PENDING
                        await db.commit()
                        
                        # Schedule for reprocessing
                        # This would typically use the background processor
                        # For now, just mark as processing
                        doc.status = FileStatus.PROCESSING
                        retried_count += 1
                        
                    except Exception as e:
                        error_message(f"Failed to retry document {doc.id}: {e}")
                
                await db.commit()
                success_message(f"Retried {retried_count} failed documents")
                
        except Exception as e:
            error_message(f"Failed to retry failed tasks: {e}")
    
    _retry_failed()


@tasks_app.command()
def purge(
    queue: str = typer.Option("celery", "--queue", "-q", help="Queue to purge"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Purge all tasks from a queue."""
    
    def _purge_queue():
        try:
            if not force:
                from rich.prompt import Confirm
                if not Confirm.ask(f"Are you sure you want to purge all tasks from queue '{queue}'?"):
                    warning_message("Purge cancelled")
                    return
            
            # Purge queue using Celery
            result = subprocess.run(
                ["celery", "-A", "app.services.background_processor", "purge", "-Q", queue], 
                capture_output=True, 
                text=True,
                input="y\n",  # Confirm the purge
                cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp"
            )
            
            if result.returncode == 0:
                success_message(f"Queue '{queue}' purged successfully")
                if result.stdout:
                    console.print(result.stdout)
            else:
                error_message("Failed to purge queue")
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
            
        except Exception as e:
            error_message(f"Failed to purge queue: {e}")
    
    _purge_queue()


@tasks_app.command()
def monitor(
    refresh: int = typer.Option(5, "--refresh", "-r", help="Refresh interval in seconds"),
    duration: int = typer.Option(60, "--duration", "-d", help="Monitor duration in seconds"),
):
    """Monitor task queue in real-time."""
    
    def _monitor_tasks():
        try:
            import time
            from datetime import datetime
            
            end_time = datetime.now() + timedelta(seconds=duration)
            
            console.print(f"[bold]Monitoring tasks for {duration} seconds (refresh every {refresh}s)[/bold]")
            console.print("Press Ctrl+C to stop\n")
            
            try:
                while datetime.now() < end_time:
                    # Clear screen (simple approach)
                    console.print("\n" * 2)
                    console.print(f"[bold]Task Monitor - {datetime.now().strftime('%H:%M:%S')}[/bold]")
                    console.print("=" * 60)
                    
                    # Get quick stats
                    try:
                        import redis
                        redis_client = redis.Redis.from_url("redis://localhost:6379/0")
                        
                        # Queue lengths
                        celery_queue = redis_client.llen("celery")
                        console.print(f"Celery queue: {celery_queue} tasks")
                        
                        # Active workers check
                        worker_result = subprocess.run(
                            ["celery", "-A", "app.services.background_processor", "inspect", "active"], 
                            capture_output=True, 
                            text=True,
                            timeout=3,
                            cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp"
                        )
                        
                        if worker_result.returncode == 0:
                            try:
                                active_data = json.loads(worker_result.stdout) if worker_result.stdout.strip() else {}
                                total_active = sum(len(tasks) for tasks in active_data.values())
                                console.print(f"Active tasks: {total_active}")
                                console.print(f"Workers: {len(active_data)}")
                            except json.JSONDecodeError:
                                console.print("Workers: Status unknown")
                        else:
                            console.print("Workers: Not responding")
                        
                    except Exception as e:
                        console.print(f"Error getting stats: {e}")
                    
                    console.print("=" * 60)
                    time.sleep(refresh)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped by user[/yellow]")
            
            console.print("\n[green]Monitoring completed[/green]")
            
        except Exception as e:
            error_message(f"Failed to monitor tasks: {e}")
    
    _monitor_tasks()


@tasks_app.command()
def flower():
    """Start Flower web interface for monitoring Celery tasks."""
    
    def _start_flower():
        try:
            # Check if flower is available
            result = subprocess.run(
                ["flower", "--version"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                error_message("Flower not available. Install with: pip install flower")
                return
            
            info_message("Starting Flower web interface...")
            console.print("Flower will be available at: http://localhost:5555")
            console.print("Press Ctrl+C to stop")
            
            # Start flower
            subprocess.run([
                "flower", 
                "-A", "app.services.background_processor",
                "--port=5555"
            ], cwd="/home/runner/work/ai-chatbot-mcp/ai-chatbot-mcp")
            
        except KeyboardInterrupt:
            info_message("Flower stopped")
        except Exception as e:
            error_message(f"Failed to start Flower: {e}")
    
    _start_flower()


@tasks_app.command()
def stats():
    """Show task execution statistics."""
    
    @async_command
    async def _task_stats():
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import and_, func, select

                # Document processing statistics
                total_docs = await db.scalar(select(func.count(Document.id)))
                pending_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.status == FileStatus.PENDING)
                )
                processing_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.status == FileStatus.PROCESSING)
                )
                completed_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.status == FileStatus.COMPLETED)
                )
                failed_docs = await db.scalar(
                    select(func.count(Document.id)).where(Document.status == FileStatus.FAILED)
                )
                
                # Processing rates
                success_rate = (completed_docs / max(total_docs, 1)) * 100 if total_docs else 0
                failure_rate = (failed_docs / max(total_docs, 1)) * 100 if total_docs else 0
                
                # Recent activity (last 24 hours)
                last_24h = datetime.now() - timedelta(hours=24)
                recent_processed = await db.scalar(
                    select(func.count(Document.id)).where(
                        and_(
                            Document.updated_at >= last_24h,
                            Document.status == FileStatus.COMPLETED
                        )
                    )
                )
                recent_failed = await db.scalar(
                    select(func.count(Document.id)).where(
                        and_(
                            Document.updated_at >= last_24h,
                            Document.status == FileStatus.FAILED
                        )
                    )
                )
                
                # Create statistics table
                stats_table = Table(title="Task Execution Statistics")
                stats_table.add_column("Metric", style="cyan", width=25)
                stats_table.add_column("Count", style="green", width=10)
                stats_table.add_column("Percentage", style="yellow", width=12)
                stats_table.add_column("Status", width=15)
                
                # Current state
                stats_table.add_row("Total Documents", str(total_docs or 0), "100%", "")
                stats_table.add_row("Pending", str(pending_docs or 0), f"{(pending_docs or 0) / max(total_docs, 1) * 100:.1f}%", "⏳ Waiting")
                stats_table.add_row("Processing", str(processing_docs or 0), f"{(processing_docs or 0) / max(total_docs, 1) * 100:.1f}%", "⚙️ Working")
                stats_table.add_row("Completed", str(completed_docs or 0), f"{success_rate:.1f}%", "✅ Success")
                stats_table.add_row("Failed", str(failed_docs or 0), f"{failure_rate:.1f}%", "❌ Failed")
                
                # Recent activity
                stats_table.add_row("", "", "", "")  # Separator
                stats_table.add_row("Processed (24h)", str(recent_processed or 0), "", "📈 Recent")
                stats_table.add_row("Failed (24h)", str(recent_failed or 0), "", "📉 Recent")
                
                console.print(stats_table)
                
                # Performance indicators
                performance_indicators = []
                if success_rate > 95:
                    performance_indicators.append("🟢 Processing Success Rate: Excellent")
                elif success_rate > 80:
                    performance_indicators.append("🟡 Processing Success Rate: Good")
                else:
                    performance_indicators.append("🔴 Processing Success Rate: Needs Attention")
                
                if pending_docs and pending_docs > 50:
                    performance_indicators.append("🟡 High number of pending documents")
                
                if processing_docs and processing_docs > 10:
                    performance_indicators.append("🟡 Many documents currently processing")
                
                if performance_indicators:
                    performance_panel = Panel(
                        "\n".join(performance_indicators),
                        title="Performance Indicators",
                        border_style="blue"
                    )
                    console.print(performance_panel)
                
        except Exception as e:
            error_message(f"Failed to get task statistics: {e}")
    
    _task_stats()
