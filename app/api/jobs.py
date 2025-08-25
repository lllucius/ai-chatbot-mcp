"""Job management API endpoints.

This module provides comprehensive REST API endpoints for managing scheduled jobs
including CRUD operations, execution tracking, and scheduling functionality.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_superuser, get_current_user
from app.models.job import JobStatus, JobType, ScheduleType
from app.models.user import User
from app.services.job_service import JobService
from app.utils.api_errors import handle_api_errors, log_api_call
from app.utils.timestamp import utcnow
from shared.schemas.common import APIResponse
from shared.schemas.job import (
    JobCreate,
    JobExecutionRequest,
    JobExecutionResponse,
    JobListResponse,
    JobResponse,
    JobScheduleValidationRequest,
    JobScheduleValidationResponse,
    JobSearchParams,
    JobStatsData,
    JobStatsResponse,
    JobUpdate,
)

router = APIRouter(tags=["jobs"])


@router.post("/", response_model=APIResponse[JobResponse])
@handle_api_errors("Failed to create job")
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobResponse]:
    """Create a new scheduled job with validation and next run calculation."""
    log_api_call("create_job", user_id=str(current_user.id), job_name=job_data.name)
    
    job_service = JobService(db)
    job = await job_service.create_job(job_data)
    
    return APIResponse[JobResponse](
        success=True,
        message=f"Job '{job.name}' created successfully",
        data=JobResponse.model_validate(job)
    )


@router.get("/", response_model=APIResponse[JobListResponse])
@handle_api_errors("Failed to list jobs")
async def list_jobs(
    query: Optional[str] = Query(None, description="Search query"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    is_overdue: Optional[bool] = Query(None, description="Filter by overdue status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobListResponse]:
    """List jobs with filtering, searching and pagination."""
    log_api_call("list_jobs", user_id=str(current_user.id), page=page, size=size)
    
    job_service = JobService(db)
    search_params = JobSearchParams(
        query=query,
        status=status,
        job_type=job_type,
        is_enabled=is_enabled,
        is_overdue=is_overdue,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    jobs, total = await job_service.list_jobs(search_params)
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    return APIResponse[JobListResponse](
        success=True,
        message=f"Retrieved {len(jobs)} jobs",
        data=JobListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total
        )
    )


@router.get("/{job_id}", response_model=APIResponse[JobResponse])
@handle_api_errors("Failed to get job")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobResponse]:
    """Get job by ID with detailed information."""
    log_api_call("get_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    job = await job_service.get_job(job_id)
    
    return APIResponse[JobResponse](
        success=True,
        message=f"Job '{job.name}' retrieved successfully",
        data=JobResponse.model_validate(job)
    )


@router.put("/{job_id}", response_model=APIResponse[JobResponse])
@handle_api_errors("Failed to update job")
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobResponse]:
    """Update job configuration with validation and schedule recalculation."""
    log_api_call("update_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    job = await job_service.update_job(job_id, job_data)
    
    return APIResponse[JobResponse](
        success=True,
        message=f"Job '{job.name}' updated successfully",
        data=JobResponse.model_validate(job)
    )


@router.delete("/{job_id}", response_model=APIResponse[dict])
@handle_api_errors("Failed to delete job")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Delete job permanently."""
    log_api_call("delete_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    
    # Get job name before deletion for response
    job = await job_service.get_job(job_id)
    job_name = job.name
    
    await job_service.delete_job(job_id)
    
    return APIResponse[dict](
        success=True,
        message=f"Job '{job_name}' deleted successfully",
        data={"job_id": job_id, "job_name": job_name}
    )


@router.post("/{job_id}/execute", response_model=APIResponse[JobExecutionResponse])
@handle_api_errors("Failed to execute job")
async def execute_job(
    job_id: int,
    execution_request: Optional[JobExecutionRequest] = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobExecutionResponse]:
    """Manually trigger job execution with optional parameter overrides."""
    log_api_call("execute_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    job = await job_service.get_job(job_id)
    
    # Check if job can be executed
    if not job.is_enabled and not (execution_request and execution_request.force):
        raise ValidationError("Job is disabled. Use force=true to execute anyway.")
    
    # Get Celery app for task scheduling
    try:
        from app.api.tasks import get_celery_app
        celery_app = get_celery_app()
    except Exception as e:
        raise ExternalServiceError(f"Task queue not available: {e}")
    
    # Prepare task arguments
    task_args = job.task_args.copy() if job.task_args else {}
    task_kwargs = job.task_kwargs.copy() if job.task_kwargs else {}
    
    # Apply overrides if provided
    if execution_request:
        if execution_request.override_args:
            task_args.update(execution_request.override_args)
        if execution_request.override_kwargs:
            task_kwargs.update(execution_request.override_kwargs)
    
    # Schedule the task
    try:
        result = celery_app.send_task(
            job.task_name,
            args=list(task_args.values()) if task_args else [],
            kwargs=task_kwargs,
            queue=job.task_queue,
            priority=job.task_priority,
            countdown=0  # Execute immediately
        )
        
        task_id = result.id
        scheduled_at = utcnow()
        
        # Update job execution tracking
        await job_service.update_job_execution(
            job_id=job.id,
            task_id=task_id,
            task_status="scheduled",
            error_message=None
        )
        
        return APIResponse[JobExecutionResponse](
            success=True,
            message=f"Job '{job.name}' execution scheduled successfully",
            data=JobExecutionResponse(
                job_id=job.id,
                task_id=task_id,
                scheduled_at=scheduled_at,
                message=f"Task scheduled in queue '{job.task_queue}'"
            )
        )
        
    except Exception as e:
        # Update job with error
        await job_service.update_job_execution(
            job_id=job.id,
            task_id="",
            task_status="failed",
            error_message=str(e)
        )
        raise ExternalServiceError(f"Failed to schedule task: {e}")


@router.post("/{job_id}/pause", response_model=APIResponse[JobResponse])
@handle_api_errors("Failed to pause job")
async def pause_job(
    job_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobResponse]:
    """Pause job execution (disable scheduling but keep configuration)."""
    log_api_call("pause_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    job_data = JobUpdate(status=JobStatus.PAUSED)
    job = await job_service.update_job(job_id, job_data)
    
    return APIResponse[JobResponse](
        success=True,
        message=f"Job '{job.name}' paused successfully",
        data=JobResponse.model_validate(job)
    )


@router.post("/{job_id}/resume", response_model=APIResponse[JobResponse])
@handle_api_errors("Failed to resume job")
async def resume_job(
    job_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobResponse]:
    """Resume paused job execution."""
    log_api_call("resume_job", user_id=str(current_user.id), job_id=job_id)
    
    job_service = JobService(db)
    job_data = JobUpdate(status=JobStatus.ACTIVE)
    job = await job_service.update_job(job_id, job_data)
    
    return APIResponse[JobResponse](
        success=True,
        message=f"Job '{job.name}' resumed successfully",
        data=JobResponse.model_validate(job)
    )


@router.get("/overdue/list", response_model=APIResponse[JobListResponse])
@handle_api_errors("Failed to get overdue jobs")
async def get_overdue_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobListResponse]:
    """Get all jobs that are overdue for execution."""
    log_api_call("get_overdue_jobs", user_id=str(current_user.id))
    
    job_service = JobService(db)
    jobs = await job_service.get_overdue_jobs()
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    return APIResponse[JobListResponse](
        success=True,
        message=f"Found {len(jobs)} overdue jobs",
        data=JobListResponse(
            jobs=job_responses,
            total=len(jobs),
            page=1,
            size=len(jobs),
            has_next=False
        )
    )


@router.get("/stats/overview", response_model=APIResponse[JobStatsResponse])
@handle_api_errors("Failed to get job statistics")
async def get_job_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobStatsResponse]:
    """Get comprehensive job statistics and metrics."""
    log_api_call("get_job_stats", user_id=str(current_user.id))
    
    job_service = JobService(db)
    stats = await job_service.get_job_stats()
    
    return APIResponse[JobStatsResponse](
        success=True,
        message="Job statistics retrieved successfully",
        data=JobStatsResponse(
            success=True,
            data=JobStatsData(**stats),
            timestamp=utcnow()
        )
    )


@router.post("/validate-schedule", response_model=APIResponse[JobScheduleValidationResponse])
@handle_api_errors("Failed to validate schedule")
async def validate_schedule(
    request: JobScheduleValidationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JobScheduleValidationResponse]:
    """Validate job schedule configuration and preview next execution times."""
    log_api_call("validate_schedule", user_id=str(current_user.id))
    
    job_service = JobService(db)
    is_valid, error_message, next_runs = job_service.validate_schedule(
        request.schedule_type,
        request.schedule_expression,
        request.timezone
    )
    
    # Generate human-readable description
    human_readable = None
    if is_valid:
        if request.schedule_type == ScheduleType.CRON:
            human_readable = f"Cron: {request.schedule_expression}"
        elif request.schedule_type == ScheduleType.INTERVAL:
            human_readable = f"Every {request.schedule_expression} minutes"
        elif request.schedule_type == ScheduleType.DAILY:
            human_readable = f"Daily at {request.schedule_expression}"
        elif request.schedule_type == ScheduleType.WEEKLY:
            parts = request.schedule_expression.split(':')
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_name = days[int(parts[0])]
            human_readable = f"Weekly on {day_name} at {parts[1]}:{parts[2]}"
        elif request.schedule_type == ScheduleType.MONTHLY:
            parts = request.schedule_expression.split(':')
            human_readable = f"Monthly on day {parts[0]} at {parts[1]}:{parts[2]}"
    
    return APIResponse[JobScheduleValidationResponse](
        success=True,
        message="Schedule validation completed",
        data=JobScheduleValidationResponse(
            is_valid=is_valid,
            error_message=error_message,
            next_runs=next_runs[:5] if next_runs else None,  # Limit to 5 runs
            human_readable=human_readable
        )
    )


# Import missing dependencies
from app.core.exceptions import ExternalServiceError, ValidationError