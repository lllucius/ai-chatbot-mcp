"""Pydantic schemas for job management API endpoints.

This module provides request and response models for job management operations,
ensuring type safety and proper API documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.job import JobStatus, JobType, ScheduleType


class JobBase(BaseModel):
    """Base job schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Unique job name")
    title: str = Field(..., min_length=1, max_length=500, description="Human-readable job title")
    description: Optional[str] = Field(None, description="Job description")
    job_type: JobType = Field(..., description="Type of job")
    
    schedule_type: ScheduleType = Field(..., description="Type of schedule")
    schedule_expression: str = Field(..., min_length=1, max_length=200, description="Schedule expression")
    timezone: str = Field(default="UTC", description="Timezone for schedule")
    
    task_name: str = Field(..., min_length=1, max_length=200, description="Task to execute")
    task_args: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task arguments")
    task_kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task keyword arguments")
    task_queue: str = Field(default="default", description="Task queue name")
    task_priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="Task timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job configuration")
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job tags")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate job name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Job name must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @field_validator('schedule_expression')
    @classmethod
    def validate_schedule_expression(cls, v: str, info) -> str:
        """Validate schedule expression based on schedule type."""
        # Basic validation - could be enhanced with more specific checks
        if not v.strip():
            raise ValueError('Schedule expression cannot be empty')
        return v.strip()


class JobCreate(JobBase):
    """Schema for creating a new job."""
    
    is_enabled: bool = Field(default=True, description="Whether job is enabled")
    status: JobStatus = Field(default=JobStatus.ACTIVE, description="Job status")


class JobUpdate(BaseModel):
    """Schema for updating an existing job."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Human-readable job title")
    description: Optional[str] = Field(None, description="Job description")
    
    schedule_type: Optional[ScheduleType] = Field(None, description="Type of schedule")
    schedule_expression: Optional[str] = Field(None, min_length=1, max_length=200, description="Schedule expression")
    timezone: Optional[str] = Field(None, description="Timezone for schedule")
    
    task_args: Optional[Dict[str, Any]] = Field(None, description="Task arguments")
    task_kwargs: Optional[Dict[str, Any]] = Field(None, description="Task keyword arguments")
    task_queue: Optional[str] = Field(None, description="Task queue name")
    task_priority: Optional[int] = Field(None, ge=1, le=10, description="Task priority (1-10)")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="Task timeout in seconds")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Maximum retry attempts")
    
    is_enabled: Optional[bool] = Field(None, description="Whether job is enabled")
    status: Optional[JobStatus] = Field(None, description="Job status")
    
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")
    tags: Optional[Dict[str, Any]] = Field(None, description="Job tags")


class JobResponse(JobBase):
    """Schema for job response data."""
    
    model_config = {"from_attributes": True}
    
    id: int = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    is_enabled: bool = Field(..., description="Whether job is enabled")
    
    # Execution tracking
    last_run_at: Optional[datetime] = Field(None, description="Last execution time")
    next_run_at: Optional[datetime] = Field(None, description="Next scheduled execution time")
    last_task_id: Optional[str] = Field(None, description="Last task ID")
    last_task_status: Optional[str] = Field(None, description="Last task status")
    last_error: Optional[str] = Field(None, description="Last error message")
    
    # Statistics
    total_runs: int = Field(..., description="Total number of runs")
    successful_runs: int = Field(..., description="Number of successful runs")
    failed_runs: int = Field(..., description="Number of failed runs")
    average_duration_seconds: Optional[float] = Field(None, description="Average execution duration")
    success_rate: float = Field(..., description="Success rate percentage")
    is_overdue: bool = Field(..., description="Whether job is overdue")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class JobListResponse(BaseModel):
    """Response schema for listing jobs."""
    
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class JobExecutionRequest(BaseModel):
    """Schema for manually triggering job execution."""
    
    override_args: Optional[Dict[str, Any]] = Field(None, description="Override task arguments")
    override_kwargs: Optional[Dict[str, Any]] = Field(None, description="Override task keyword arguments")
    force: bool = Field(default=False, description="Force execution even if disabled")


class JobExecutionResponse(BaseModel):
    """Schema for job execution response."""
    
    job_id: int = Field(..., description="Job ID")
    task_id: str = Field(..., description="Generated task ID")
    scheduled_at: datetime = Field(..., description="When the task was scheduled")
    message: str = Field(..., description="Execution message")


class JobStatsData(BaseModel):
    """Job statistics data model."""
    
    total_jobs: int = Field(..., description="Total number of jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    paused_jobs: int = Field(..., description="Number of paused jobs")
    disabled_jobs: int = Field(..., description="Number of disabled jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    
    total_executions: int = Field(..., description="Total job executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    
    average_success_rate: float = Field(..., description="Overall success rate")
    jobs_overdue: int = Field(..., description="Number of overdue jobs")
    
    executions_last_24h: int = Field(..., description="Executions in last 24 hours")
    executions_last_7d: int = Field(..., description="Executions in last 7 days")


class JobStatsResponse(BaseModel):
    """Job statistics response schema."""
    
    success: bool = Field(..., description="Operation success status")
    data: JobStatsData = Field(..., description="Job statistics")
    timestamp: datetime = Field(..., description="Statistics timestamp")


class JobScheduleValidationRequest(BaseModel):
    """Schema for validating job schedules."""
    
    schedule_type: ScheduleType = Field(..., description="Type of schedule")
    schedule_expression: str = Field(..., description="Schedule expression to validate")
    timezone: str = Field(default="UTC", description="Timezone for schedule")


class JobScheduleValidationResponse(BaseModel):
    """Schema for schedule validation response."""
    
    is_valid: bool = Field(..., description="Whether schedule is valid")
    error_message: Optional[str] = Field(None, description="Validation error if invalid")
    next_runs: Optional[List[datetime]] = Field(None, description="Next few execution times if valid")
    human_readable: Optional[str] = Field(None, description="Human-readable schedule description")


class JobSearchParams(BaseModel):
    """Parameters for searching jobs."""
    
    query: Optional[str] = Field(None, description="Search query")
    status: Optional[JobStatus] = Field(None, description="Filter by status")
    job_type: Optional[JobType] = Field(None, description="Filter by job type")
    is_enabled: Optional[bool] = Field(None, description="Filter by enabled status")
    is_overdue: Optional[bool] = Field(None, description="Filter by overdue status")
    tags: Optional[Dict[str, Any]] = Field(None, description="Filter by tags")
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")