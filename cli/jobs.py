"""Job management commands for the AI Chatbot Platform CLI.

This module provides comprehensive management of scheduled jobs through async 
operations and the AI Chatbot SDK for creating, monitoring, and controlling
job schedules and execution.
"""

from typing import Optional

from async_typer import AsyncTyper
from typer import Argument, Option

from cli.base import error_message, get_sdk, success_message

jobs_app = AsyncTyper(
    help="Job management commands", rich_markup_mode=None
)


@jobs_app.async_command()
async def list(
    status: Optional[str] = Option(None, "--status", help="Filter by status (active/paused/disabled/failed)"),
    job_type: Optional[str] = Option(None, "--type", help="Filter by job type"),
    enabled_only: bool = Option(False, "--enabled-only", help="Show only enabled jobs"),
    overdue_only: bool = Option(False, "--overdue-only", help="Show only overdue jobs"),
    page: int = Option(1, "--page", help="Page number"),
    size: int = Option(20, "--size", help="Page size"),
):
    """List scheduled jobs with filtering options."""
    try:
        sdk = await get_sdk()
        params = {
            "page": page,
            "size": size
        }
        
        if status:
            params["status"] = status
        if job_type:
            params["job_type"] = job_type
        if enabled_only:
            params["is_enabled"] = True
        if overdue_only:
            params["is_overdue"] = True
            
        data = await sdk.jobs.list(**params)
        if data:
            jobs = data.get("jobs", [])
            total = data.get("total", 0)
            
            if not jobs:
                print("No jobs found")
                return
            
            # Convert to table data
            job_data = []
            for job in jobs:
                status_indicator = "🟢" if job.get("is_enabled") else "🔴"
                overdue_indicator = "⚠️" if job.get("is_overdue") else ""
                
                job_data.append({
                    "ID": str(job.get("id", "")),
                    "Name": job.get("name", ""),
                    "Type": job.get("job_type", ""),
                    "Status": f"{status_indicator} {job.get('status', '')}",
                    "Schedule": job.get("schedule_expression", ""),
                    "Last Run": job.get("last_run_at", "Never")[:19] if job.get("last_run_at") else "Never",
                    "Next Run": job.get("next_run_at", "N/A")[:19] if job.get("next_run_at") else "N/A",
                    "Success Rate": f"{job.get('success_rate', 0):.1f}%",
                    "Overdue": overdue_indicator
                })
            
            from cli.base import display_rich_table
            
            display_rich_table(job_data, f"Scheduled Jobs ({total} total)")
            
            if data.get("has_next", False):
                print(f"\nShowing page {page} of results. Use --page {page + 1} to see more.")
                
    except Exception as e:
        error_message(f"Failed to list jobs: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def show(
    job_id: int = Argument(..., help="Job ID to display"),
):
    """Show detailed information about a specific job."""
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.get(job_id)
        if data:
            print(f"\nJob Details: {data.get('name', '')}")
            print("=" * (len(data.get('name', '')) + 13))
            print(f"ID: {data.get('id', '')}")
            print(f"Title: {data.get('title', '')}")
            print(f"Description: {data.get('description', 'N/A')}")
            print(f"Type: {data.get('job_type', '')}")
            print(f"Status: {data.get('status', '')} ({'Enabled' if data.get('is_enabled') else 'Disabled'})")
            print()
            
            print("Schedule Configuration:")
            print(f"  Type: {data.get('schedule_type', '')}")
            print(f"  Expression: {data.get('schedule_expression', '')}")
            print(f"  Timezone: {data.get('timezone', 'UTC')}")
            print()
            
            print("Task Configuration:")
            print(f"  Task Name: {data.get('task_name', '')}")
            print(f"  Queue: {data.get('task_queue', 'default')}")
            print(f"  Priority: {data.get('task_priority', 5)}")
            print(f"  Timeout: {data.get('timeout_seconds', 'N/A')} seconds")
            print(f"  Max Retries: {data.get('max_retries', 3)}")
            print()
            
            print("Execution Status:")
            print(f"  Last Run: {data.get('last_run_at', 'Never')}")
            print(f"  Next Run: {data.get('next_run_at', 'N/A')}")
            print(f"  Last Task ID: {data.get('last_task_id', 'N/A')}")
            print(f"  Last Task Status: {data.get('last_task_status', 'N/A')}")
            print(f"  Is Overdue: {'Yes' if data.get('is_overdue') else 'No'}")
            print()
            
            print("Statistics:")
            print(f"  Total Runs: {data.get('total_runs', 0)}")
            print(f"  Successful: {data.get('successful_runs', 0)}")
            print(f"  Failed: {data.get('failed_runs', 0)}")
            print(f"  Success Rate: {data.get('success_rate', 0):.2f}%")
            print(f"  Avg Duration: {data.get('average_duration_seconds', 0):.2f}s")
            
            if data.get('last_error'):
                print(f"\nLast Error: {data.get('last_error')}")
            print()
            
    except Exception as e:
        error_message(f"Failed to get job details: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def create(
    name: str = Argument(..., help="Job name (unique identifier)"),
    title: str = Argument(..., help="Human-readable job title"),
    job_type: str = Argument(..., help="Job type"),
    schedule_type: str = Argument(..., help="Schedule type (cron/interval/daily/weekly/monthly)"),
    schedule_expression: str = Argument(..., help="Schedule expression"),
    task_name: str = Argument(..., help="Task name to execute"),
    description: Optional[str] = Option(None, "--description", help="Job description"),
    timezone: str = Option("UTC", "--timezone", help="Timezone for schedule"),
    task_queue: str = Option("default", "--queue", help="Task queue"),
    task_priority: int = Option(5, "--priority", help="Task priority (1-10)"),
    timeout_seconds: Optional[int] = Option(None, "--timeout", help="Task timeout in seconds"),
    max_retries: int = Option(3, "--max-retries", help="Maximum retry attempts"),
    enabled: bool = Option(True, "--enabled/--disabled", help="Enable job"),
):
    """Create a new scheduled job."""
    try:
        sdk = await get_sdk()
        job_data = {
            "name": name,
            "title": title,
            "job_type": job_type,
            "schedule_type": schedule_type,
            "schedule_expression": schedule_expression,
            "task_name": task_name,
            "timezone": timezone,
            "task_queue": task_queue,
            "task_priority": task_priority,
            "max_retries": max_retries,
            "is_enabled": enabled
        }
        
        if description:
            job_data["description"] = description
        if timeout_seconds:
            job_data["timeout_seconds"] = timeout_seconds
            
        data = await sdk.jobs.create(job_data)
        if data:
            success_message(f"Job '{name}' created successfully with ID {data.get('id')}")
            
    except Exception as e:
        error_message(f"Failed to create job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def update(
    job_id: int = Argument(..., help="Job ID to update"),
    title: Optional[str] = Option(None, "--title", help="New title"),
    description: Optional[str] = Option(None, "--description", help="New description"),
    schedule_expression: Optional[str] = Option(None, "--schedule", help="New schedule expression"),
    timezone: Optional[str] = Option(None, "--timezone", help="New timezone"),
    task_priority: Optional[int] = Option(None, "--priority", help="New task priority"),
    timeout_seconds: Optional[int] = Option(None, "--timeout", help="New timeout"),
    max_retries: Optional[int] = Option(None, "--max-retries", help="New max retries"),
    enabled: Optional[bool] = Option(None, "--enabled/--disabled", help="Enable/disable job"),
):
    """Update an existing job."""
    try:
        sdk = await get_sdk()
        update_data = {}
        
        if title:
            update_data["title"] = title
        if description:
            update_data["description"] = description
        if schedule_expression:
            update_data["schedule_expression"] = schedule_expression
        if timezone:
            update_data["timezone"] = timezone
        if task_priority:
            update_data["task_priority"] = task_priority
        if timeout_seconds:
            update_data["timeout_seconds"] = timeout_seconds
        if max_retries:
            update_data["max_retries"] = max_retries
        if enabled is not None:
            update_data["is_enabled"] = enabled
            
        if not update_data:
            error_message("No update parameters provided")
            raise SystemExit(1)
            
        data = await sdk.jobs.update(job_id, update_data)
        if data:
            success_message(f"Job '{data.get('name')}' updated successfully")
            
    except Exception as e:
        error_message(f"Failed to update job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def delete(
    job_id: int = Argument(..., help="Job ID to delete"),
    force: bool = Option(False, "--force", help="Skip confirmation"),
):
    """Delete a job permanently."""
    from cli.base import confirm_action
    
    if not force:
        try:
            sdk = await get_sdk()
            job_data = await sdk.jobs.get(job_id)
            job_name = job_data.get('name', f'ID {job_id}') if job_data else f'ID {job_id}'
        except:
            job_name = f'ID {job_id}'
            
        if not confirm_action(f"Are you sure you want to delete job '{job_name}'?"):
            return
    
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.delete(job_id)
        if data:
            success_message(f"Job '{data.get('job_name', job_id)}' deleted successfully")
            
    except Exception as e:
        error_message(f"Failed to delete job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def execute(
    job_id: int = Argument(..., help="Job ID to execute"),
    force: bool = Option(False, "--force", help="Force execution even if disabled"),
):
    """Manually trigger job execution."""
    try:
        sdk = await get_sdk()
        execution_data = {"force": force}
        
        data = await sdk.jobs.execute(job_id, execution_data)
        if data:
            success_message(f"Job execution started: Task ID {data.get('task_id')}")
            print(f"Message: {data.get('message', '')}")
            
    except Exception as e:
        error_message(f"Failed to execute job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def pause(
    job_id: int = Argument(..., help="Job ID to pause"),
):
    """Pause job execution."""
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.pause(job_id)
        if data:
            success_message(f"Job '{data.get('name')}' paused successfully")
            
    except Exception as e:
        error_message(f"Failed to pause job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def resume(
    job_id: int = Argument(..., help="Job ID to resume"),
):
    """Resume paused job execution."""
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.resume(job_id)
        if data:
            success_message(f"Job '{data.get('name')}' resumed successfully")
            
    except Exception as e:
        error_message(f"Failed to resume job: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def overdue():
    """List all overdue jobs."""
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.get_overdue()
        if data:
            jobs = data.get("jobs", [])
            
            if not jobs:
                print("No overdue jobs found")
                return
            
            # Convert to table data
            job_data = []
            for job in jobs:
                job_data.append({
                    "ID": str(job.get("id", "")),
                    "Name": job.get("name", ""),
                    "Type": job.get("job_type", ""),
                    "Next Run": job.get("next_run_at", "")[:19] if job.get("next_run_at") else "N/A",
                    "Last Run": job.get("last_run_at", "Never")[:19] if job.get("last_run_at") else "Never",
                    "Success Rate": f"{job.get('success_rate', 0):.1f}%"
                })
            
            from cli.base import display_rich_table
            
            display_rich_table(job_data, f"Overdue Jobs ({len(jobs)} total)")
            
    except Exception as e:
        error_message(f"Failed to get overdue jobs: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command()
async def stats():
    """Show job statistics and metrics."""
    try:
        sdk = await get_sdk()
        data = await sdk.jobs.get_stats()
        if data:
            stats = data.get("data", {})
            
            print("\nJob Statistics:")
            print("===============")
            print(f"Total Jobs: {stats.get('total_jobs', 0)}")
            print(f"Active: {stats.get('active_jobs', 0)}")
            print(f"Paused: {stats.get('paused_jobs', 0)}")
            print(f"Disabled: {stats.get('disabled_jobs', 0)}")
            print(f"Failed: {stats.get('failed_jobs', 0)}")
            print(f"Overdue: {stats.get('jobs_overdue', 0)}")
            print()
            
            print("Execution Statistics:")
            print("====================")
            print(f"Total Executions: {stats.get('total_executions', 0)}")
            print(f"Successful: {stats.get('successful_executions', 0)}")
            print(f"Failed: {stats.get('failed_executions', 0)}")
            print(f"Success Rate: {stats.get('average_success_rate', 0):.2f}%")
            print()
            
            print("Recent Activity:")
            print("===============")
            print(f"Last 24 hours: {stats.get('executions_last_24h', 0)} executions")
            print(f"Last 7 days: {stats.get('executions_last_7d', 0)} executions")
            print()
            
    except Exception as e:
        error_message(f"Failed to get job statistics: {str(e)}")
        raise SystemExit(1)


@jobs_app.async_command("validate-schedule")
async def validate_schedule(
    schedule_type: str = Argument(..., help="Schedule type (cron/interval/daily/weekly/monthly)"),
    schedule_expression: str = Argument(..., help="Schedule expression to validate"),
    timezone: str = Option("UTC", "--timezone", help="Timezone for validation"),
):
    """Validate a schedule expression and preview next execution times."""
    try:
        sdk = await get_sdk()
        validation_data = {
            "schedule_type": schedule_type,
            "schedule_expression": schedule_expression,
            "timezone": timezone
        }
        
        data = await sdk.jobs.validate_schedule(validation_data)
        if data:
            result = data.get("data", {})
            
            if result.get("is_valid"):
                success_message("Schedule is valid!")
                print(f"Description: {result.get('human_readable', 'N/A')}")
                
                next_runs = result.get("next_runs", [])
                if next_runs:
                    print("\nNext 5 execution times:")
                    for i, run_time in enumerate(next_runs[:5], 1):
                        print(f"  {i}. {run_time}")
                print()
            else:
                error_message(f"Invalid schedule: {result.get('error_message', 'Unknown error')}")
                
    except Exception as e:
        error_message(f"Failed to validate schedule: {str(e)}")
        raise SystemExit(1)