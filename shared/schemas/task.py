"""Pydantic response schemas for task management API endpoints.

This module provides response models for all task-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskSystemStatusData(BaseModel):
    """Task system status data model."""

    broker_status: str = Field(..., description="Message broker connectivity status")
    active_workers: int = Field(..., description="Number of active workers")
    active_tasks: int = Field(..., description="Number of currently active tasks")
    reserved_tasks: int = Field(..., description="Number of reserved tasks in queue")
    system_status: str = Field(..., description="Overall system health status")
    timestamp: str = Field(..., description="Status timestamp")
    error: Optional[str] = Field(
        default=None, description="Error message if status unavailable"
    )


class TaskSystemStatusResponse(BaseModel):
    """Task system status response schema."""

    success: bool = Field(..., description="Operation success status")
    data: TaskSystemStatusData = Field(..., description="Task system status data")


class WorkerInfo(BaseModel):
    """Individual worker information model."""

    name: str = Field(..., description="Worker name/hostname")
    status: str = Field(..., description="Worker status")
    pool: str = Field(..., description="Worker pool implementation type")
    processes: int = Field(..., description="Number of worker processes")
    max_concurrency: int = Field(..., description="Maximum concurrent task capacity")
    current_load: int = Field(..., description="Current task execution load")
    broker_transport: str = Field(..., description="Message broker transport mechanism")
    prefetch_count: int = Field(..., description="Task prefetch multiplier setting")
    last_heartbeat: str = Field(
        ..., description="Most recent worker heartbeat timestamp"
    )


class WorkerStatusData(BaseModel):
    """Worker status data model."""

    workers: List[WorkerInfo] = Field(
        default_factory=list, description="List of worker information"
    )
    total_workers: int = Field(..., description="Total number of workers")
    online_workers: int = Field(..., description="Number of online workers")
    timestamp: str = Field(..., description="Status timestamp")


class WorkerStatusResponse(BaseModel):
    """Worker status response schema."""

    success: bool = Field(..., description="Operation success status")
    data: WorkerStatusData = Field(..., description="Worker status data")


class TaskInfo(BaseModel):
    """Individual task information model."""

    id: Optional[str] = Field(default=None, description="Task identifier")
    name: Optional[str] = Field(default=None, description="Task name")
    args: List[Any] = Field(default_factory=list, description="Task arguments")
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Task keyword arguments"
    )
    worker: str = Field(..., description="Assigned worker")
    status: str = Field(..., description="Task status")


class QueueInfo(BaseModel):
    """Queue information model."""

    name: str = Field(..., description="Queue name")
    active: int = Field(..., description="Number of active tasks")
    reserved: int = Field(..., description="Number of reserved tasks")
    scheduled: int = Field(..., description="Number of scheduled tasks")
    tasks: List[TaskInfo] = Field(
        default_factory=list, description="List of tasks in queue"
    )


class QueueStatusData(BaseModel):
    """Queue status data model."""

    queues: List[QueueInfo] = Field(
        default_factory=list, description="List of queue information"
    )
    total_queues: int = Field(..., description="Total number of queues")
    filtered_by: Optional[str] = Field(default=None, description="Queue filter applied")
    timestamp: str = Field(..., description="Status timestamp")


class QueueStatusResponse(BaseModel):
    """Queue status response schema."""

    success: bool = Field(..., description="Operation success status")
    data: QueueStatusData = Field(..., description="Queue status data")


class ActiveTaskInfo(BaseModel):
    """Active task information model."""

    id: Optional[str] = Field(default=None, description="Task identifier")
    name: Optional[str] = Field(default=None, description="Task name")
    args: List[Any] = Field(default_factory=list, description="Task arguments")
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Task keyword arguments"
    )
    worker: str = Field(..., description="Worker hostname")
    time_start: Optional[str] = Field(default=None, description="Task start timestamp")
    acknowledged: bool = Field(default=False, description="Task acknowledgment status")
    delivery_info: Dict[str, Any] = Field(
        default_factory=dict, description="Message delivery info"
    )


class ActiveTasksData(BaseModel):
    """Active tasks data model."""

    active_tasks: List[ActiveTaskInfo] = Field(
        default_factory=list, description="List of active tasks"
    )
    total_active: int = Field(..., description="Total number of active tasks")
    workers_with_tasks: int = Field(
        ..., description="Number of workers with active tasks"
    )
    timestamp: str = Field(..., description="Status timestamp")


class ActiveTasksResponse(BaseModel):
    """Active tasks response schema."""

    success: bool = Field(..., description="Operation success status")
    data: ActiveTasksData = Field(..., description="Active tasks data")


class DocumentProcessingStats(BaseModel):
    """Document processing statistics model."""

    total: int = Field(..., description="Total number of documents")
    completed: int = Field(
        ..., description="Number of successfully completed documents"
    )
    failed: int = Field(..., description="Number of documents that failed processing")
    processing: int = Field(
        ..., description="Number of documents currently being processed"
    )
    success_rate: float = Field(
        ..., description="Percentage of successful processing operations"
    )
    failure_rate: float = Field(
        ..., description="Percentage of failed processing operations"
    )
    avg_processing_time_seconds: float = Field(
        ..., description="Average processing duration"
    )


class TaskStatisticsData(BaseModel):
    """Task statistics data model."""

    period_hours: int = Field(..., description="Analysis period in hours")
    start_time: str = Field(..., description="Analysis period start timestamp")
    document_processing: DocumentProcessingStats = Field(
        ..., description="Document processing statistics"
    )
    recent_errors: List[str] = Field(
        default_factory=list, description="Sample of recent error messages"
    )
    timestamp: str = Field(..., description="Statistics timestamp")


class TaskStatisticsResponse(BaseModel):
    """Task statistics response schema."""

    success: bool = Field(..., description="Operation success status")
    data: TaskStatisticsData = Field(..., description="Task statistics data")


class TasksSummary(BaseModel):
    """Summary of active tasks for monitoring."""

    count: int = Field(..., description="Number of active tasks")
    workers_busy: int = Field(..., description="Number of workers with active tasks")


class WorkersSummary(BaseModel):
    """Summary of workers for monitoring."""

    total: int = Field(..., description="Total number of workers")
    online: int = Field(..., description="Number of online workers")


class TaskMonitoringData(BaseModel):
    """Task monitoring data model."""

    system_status: Dict[str, Any] = Field(..., description="System status information")
    active_tasks: TasksSummary = Field(..., description="Active tasks summary")
    workers: WorkersSummary = Field(..., description="Workers summary")
    recent_performance: Dict[str, Any] = Field(
        ..., description="Recent performance metrics"
    )
    timestamp: str = Field(..., description="Monitoring timestamp")
    refresh_interval: int = Field(
        default=30, description="Suggested refresh interval in seconds"
    )


class TaskMonitoringResponse(BaseModel):
    """Task monitoring response schema."""

    success: bool = Field(..., description="Operation success status")
    data: TaskMonitoringData = Field(..., description="Task monitoring data")


# Profile-related response models for profiles.py
class ProfileParametersData(BaseModel):
    """Profile parameters data model."""

    parameters: Dict[str, Any] = Field(..., description="Profile parameters")
    profile_name: str = Field(..., description="Profile name")


class ProfileParametersResponse(BaseModel):
    """Profile parameters response schema."""

    success: bool = Field(..., description="Operation success status")
    data: ProfileParametersData = Field(..., description="Profile parameters data")


class ProfileStatisticsData(BaseModel):
    """Profile statistics data model."""

    total_profiles: int = Field(..., description="Total number of profiles")
    active_profiles: int = Field(..., description="Number of active profiles")
    usage_stats: Dict[str, Any] = Field(
        default_factory=dict, description="Profile usage statistics"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics"
    )
    timestamp: str = Field(..., description="Statistics timestamp")


class ProfileStatisticsResponse(BaseModel):
    """Profile statistics response schema."""

    success: bool = Field(..., description="Operation success status")
    data: ProfileStatisticsData = Field(..., description="Profile statistics data")


class ProfileValidationData(BaseModel):
    """Profile validation data model."""

    valid: bool = Field(..., description="Whether the parameters are valid")
    errors: List[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="The validated parameters"
    )


class ProfileValidationResponse(BaseModel):
    """Profile validation response schema."""

    success: bool = Field(..., description="Operation success status")
    data: ProfileValidationData = Field(..., description="Profile validation data")


class DefaultProfileResponse(BaseModel):
    """Default profile response schema for the specific endpoint that returns default profile params."""

    success: bool = Field(..., description="Operation success status")
    data: ProfileParametersData = Field(
        ..., description="Default profile parameters data"
    )
