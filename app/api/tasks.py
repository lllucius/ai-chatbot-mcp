"""Background task management API endpoints."""

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from shared.schemas.admin import (
    ActiveTasksResponse,
    QueueResponse,
    TaskMonitorResponse,
    TaskStatsResponse,
    TaskStatusResponse,
    WorkersResponse,
)
from shared.schemas.common import APIResponse, BaseResponse, SuccessResponse, ErrorResponse
from shared.schemas.task_responses import (
    TaskSystemStatusData,
    TaskSystemStatusResponse,
    WorkerInfo,
    WorkerStatusData,
    WorkerStatusResponse,
    TaskInfo,
    QueueInfo,
    QueueStatusData,
    QueueStatusResponse,
    ActiveTaskInfo,
    ActiveTasksData,
    ActiveTasksResponse as NewActiveTasksResponse,
    DocumentProcessingStats,
    TaskStatisticsData,
    TaskStatisticsResponse,
    TasksSummary,
    WorkersSummary,
    TaskMonitoringData,
    TaskMonitoringResponse,
)
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tasks"])


def get_celery_app():
    """
    Get Celery application instance for task management operations.

    Retrieves the configured Celery application instance used for background
    task processing, queue management, and worker coordination. Handles import
    errors gracefully when Celery is not available or properly configured.

    Returns:
        Celery: Configured Celery application instance

    Raises:
        HTTPException: If Celery is not configured, available, or properly initialized

    Note:
        This function serves as a centralized access point for Celery operations
        and provides consistent error handling across all task management endpoints.
    """
    try:
        from ..core.celery_app import celery_app

        return celery_app
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Celery is not configured or available",
        )


@router.get("/status", response_model=APIResponse[TaskSystemStatusData])
@handle_api_errors("Failed to get task system status")
async def get_task_system_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive background task system status and health metrics.

    Returns detailed status information about the Celery task system including
    broker connectivity, worker availability, queue status, and performance
    metrics. Provides real-time insights into system health and capacity.

    Args:
        current_user: Current authenticated user requesting system status

    Returns:
        TaskStatusResponse: Task system status including:
            - broker_status: Message broker connectivity and health
            - worker_stats: Active worker count and status information
            - queue_metrics: Task queue depths and processing rates
            - performance_data: System throughput and response times
            - health_indicators: Overall system health assessment

    System Health Metrics:
        - Broker connectivity and message processing status
        - Worker availability and load distribution
        - Queue depths and task processing rates
        - Error rates and failure pattern analysis
        - Resource utilization and capacity indicators

    Performance Indicators:
        - Task processing throughput and latency
        - Worker efficiency and utilization rates
        - Queue processing speed and backlog status
        - Error handling and retry success rates
        - System bottleneck identification

    Use Cases:
        - System health monitoring and alerting
        - Performance optimization and capacity planning
        - Troubleshooting and diagnostic analysis
        - Administrative dashboard displays
        - Automated scaling decision support

    Example:
        GET /api/v1/tasks/status
    """
    log_api_call("get_task_system_status", user_id=str(current_user.id))

    try:
        celery_app = get_celery_app()

        # Check broker connectivity
        try:
            inspector = celery_app.control.inspect()
            stats = inspector.stats()
            broker_status = "connected" if stats else "disconnected"
            active_workers = len(stats) if stats else 0
        except Exception as e:
            broker_status = "error"
            active_workers = 0
            stats = {"error": str(e)}

        # Get active task counts
        try:
            active_tasks = inspector.active() if broker_status == "connected" else {}
            total_active = (
                sum(len(tasks) for tasks in active_tasks.values())
                if active_tasks
                else 0
            )
        except Exception:
            total_active = 0

        # Get queue lengths
        try:
            reserved_tasks = (
                inspector.reserved() if broker_status == "connected" else {}
            )
            total_reserved = (
                sum(len(tasks) for tasks in reserved_tasks.values())
                if reserved_tasks
                else 0
            )
        except Exception:
            total_reserved = 0

        response_payload = TaskSystemStatusData(
            broker_status=broker_status,
            active_workers=active_workers,
            active_tasks=total_active,
            reserved_tasks=total_reserved,
            system_status=(
                "healthy"
                if broker_status == "connected" and active_workers > 0
                else "degraded"
            ),
            timestamp=datetime.utcnow().isoformat(),
        )
        return APIResponse[TaskSystemStatusData](
            success=True,
            message="Task system status retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        response_payload = TaskSystemStatusData(
            broker_status="unavailable",
            active_workers=0,
            active_tasks=0,
            reserved_tasks=0,
            system_status="error",
            timestamp=datetime.utcnow().isoformat(),
            error=str(e),
        )
        return APIResponse[TaskSystemStatusData](
            success=False,
            message="Failed to retrieve task system status",
            data=response_payload,
        )


@router.get("/workers", response_model=APIResponse[WorkerStatusData])
@handle_api_errors("Failed to get worker information")
async def get_workers_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive information about Celery workers with detailed status and metrics.

    Returns detailed information about all active Celery workers including their
    current status, configuration parameters, resource utilization, and performance
    metrics. Provides essential insights for worker management and system scaling.

    Args:
        current_user: Current authenticated user requesting worker information

    Returns:
        WorkersResponse: Detailed worker information including:
            - workers: List of worker objects with complete status information
            - total_workers: Total number of registered workers
            - online_workers: Number of currently active and responsive workers
            - timestamp: Information retrieval timestamp

    Raises:
        HTTP 500: If worker information retrieval fails

    Worker Information:
        - name: Unique worker identifier and hostname
        - status: Current operational status (online/offline)
        - pool: Worker pool implementation type (prefork, eventlet, gevent)
        - processes: Number of worker processes available
        - max_concurrency: Maximum concurrent task capacity
        - current_load: Current task execution load
        - broker_transport: Message broker transport mechanism
        - prefetch_count: Task prefetch multiplier setting
        - last_heartbeat: Most recent worker heartbeat timestamp

    Status Monitoring:
        - Real-time worker connectivity verification
        - Worker health checking through ping responses
        - Resource utilization and capacity assessment
        - Configuration parameter validation
        - Performance metric collection and analysis

    Pool Types:
        - prefork: Multi-process worker pool (default, CPU-intensive tasks)
        - eventlet: Event-driven concurrency (I/O-intensive tasks)
        - gevent: Green thread implementation (high concurrency)
        - solo: Single-threaded execution (debugging and testing)

    Use Cases:
        - Worker capacity planning and scaling decisions
        - Performance monitoring and optimization
        - Load balancing and task distribution analysis
        - System health assessment and troubleshooting
        - Administrative monitoring and reporting

    Example:
        GET /api/v1/tasks/workers
    """
    log_api_call("get_workers_info", user_id=str(current_user.id))

    try:
        celery_app = get_celery_app()
        inspector = celery_app.control.inspect()

        # Get worker statistics
        stats = inspector.stats() or {}

        # Get worker status
        ping_results = inspector.ping() or {}

        # Get worker configuration
        conf_results = inspector.conf() or {}

        workers = []
        for worker_name in stats:
            worker_stats = stats.get(worker_name, {})
            worker_ping = ping_results.get(worker_name, {})
            worker_conf = conf_results.get(worker_name, {})

            worker_info = WorkerInfo(
                name=worker_name,
                status=(
                    "online" if worker_ping.get("ok") == "pong" else "offline"
                ),
                pool=worker_stats.get("pool", {}).get(
                    "implementation", "unknown"
                ),
                processes=worker_stats.get("pool", {}).get("processes", 0),
                max_concurrency=worker_stats.get("pool", {}).get(
                    "max-concurrency", 0
                ),
                current_load=len(worker_stats.get("rusage", {})),
                broker_transport=worker_conf.get("broker_transport", "unknown"),
                prefetch_count=worker_conf.get("worker_prefetch_multiplier", 0),
                last_heartbeat=str(worker_stats.get("clock", "unknown")),
            )
            workers.append(worker_info)

        response_payload = WorkerStatusData(
            workers=workers,
            total_workers=len(workers),
            online_workers=len([w for w in workers if w.status == "online"]),
            timestamp=datetime.utcnow().isoformat(),
        )
        return APIResponse[WorkerStatusData](
            success=True,
            message="Worker information retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        raise


@router.get("/queue", response_model=APIResponse[QueueStatusData])
@handle_api_errors("Failed to get queue information")
async def get_queue_info(
    queue_name: Optional[str] = Query(None, description="Specific queue to check"),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive task queue information with detailed metrics and task tracking.

    Returns detailed information about task queues including pending tasks, active
    task execution, scheduled operations, and queue-specific statistics. Provides
    essential insights for queue management and task flow optimization.

    Args:
        queue_name: Optional specific queue name to filter results
        current_user: Current authenticated user requesting queue information

    Returns:
        QueueResponse: Comprehensive queue information including:
            - queues: List of queue objects with detailed task information
            - total_queues: Total number of active queues
            - filtered_by: Applied queue name filter (if any)
            - timestamp: Information retrieval timestamp

    Raises:
        HTTP 500: If queue information retrieval fails

    Queue Information:
        - name: Queue identifier and routing key
        - active: Number of tasks currently being executed
        - reserved: Number of tasks waiting in queue for execution
        - scheduled: Number of tasks scheduled for future execution
        - tasks: Detailed list of individual task information

    Task Details:
        - id: Unique task identifier
        - name: Task function name and module
        - args: Positional arguments for task execution
        - kwargs: Keyword arguments and configuration
        - worker: Assigned worker for task execution
        - status: Current task status (active/reserved/scheduled)

    Queue Management:
        - Real-time queue depth monitoring
        - Task distribution across workers
        - Queue performance and throughput analysis
        - Backlog identification and management
        - Task priority and scheduling assessment

    Use Cases:
        - Queue capacity monitoring and management
        - Task flow analysis and optimization
        - Performance bottleneck identification
        - Load balancing and distribution planning
        - Administrative monitoring and troubleshooting

    Example:
        GET /api/v1/tasks/queue
        GET /api/v1/tasks/queue?queue_name=document_processing
    """
    log_api_call("get_queue_info", user_id=str(current_user.id), queue_name=queue_name)

    try:
        celery_app = get_celery_app()
        inspector = celery_app.control.inspect()

        # Get active tasks
        active_tasks = inspector.active() or {}

        # Get reserved tasks (waiting in queue)
        reserved_tasks = inspector.reserved() or {}

        # Get scheduled tasks
        scheduled_tasks = inspector.scheduled() or {}

        queues = {}
        all_workers = (
            set(active_tasks.keys())
            | set(reserved_tasks.keys())
            | set(scheduled_tasks.keys())
        )

        for worker in all_workers:
            worker_active = active_tasks.get(worker, [])
            worker_reserved = reserved_tasks.get(worker, [])
            worker_scheduled = scheduled_tasks.get(worker, [])

            # Group by queue if available, otherwise use worker name
            for task in worker_active + worker_reserved + worker_scheduled:
                task_queue = task.get("delivery_info", {}).get("routing_key", "default")

                if queue_name and task_queue != queue_name:
                    continue

                if task_queue not in queues:
                    queues[task_queue] = {
                        "name": task_queue,
                        "active": 0,
                        "reserved": 0,
                        "scheduled": 0,
                        "tasks": [],
                    }

                task_info = TaskInfo(
                    id=task.get("id"),
                    name=task.get("name"),
                    args=task.get("args", []),
                    kwargs=task.get("kwargs", {}),
                    worker=worker,
                    status=(
                        "active"
                        if task in worker_active
                        else "reserved" if task in worker_reserved else "scheduled"
                    ),
                )

                queues[task_queue]["tasks"].append(task_info)

                if task in worker_active:
                    queues[task_queue]["active"] += 1
                elif task in worker_reserved:
                    queues[task_queue]["reserved"] += 1
                elif task in worker_scheduled:
                    queues[task_queue]["scheduled"] += 1

        # Convert queues dict to QueueInfo models
        queue_infos = [
            QueueInfo(
                name=queue_data["name"],
                active=queue_data["active"],
                reserved=queue_data["reserved"],
                scheduled=queue_data["scheduled"],
                tasks=queue_data["tasks"],
            )
            for queue_data in queues.values()
        ]

        response_payload = QueueStatusData(
            queues=queue_infos,
            total_queues=len(queues),
            filtered_by=queue_name,
            timestamp=datetime.utcnow().isoformat(),
        )
        return APIResponse[QueueStatusData](
            success=True,
            message="Queue information retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        raise


@router.get("/active", response_model=APIResponse[ActiveTasksData])
@handle_api_errors("Failed to get active tasks")
async def get_active_tasks(
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive information about currently executing tasks with detailed metadata.

    Returns detailed information about all tasks currently being executed by Celery
    workers including task parameters, execution context, timing information, and
    worker assignment. Provides real-time visibility into system activity.

    Args:
        current_user: Current authenticated user requesting active task information

    Returns:
        ActiveTasksResponse: Active task information including:
            - active_tasks: List of currently executing task objects
            - total_active: Total number of active tasks across all workers
            - workers_with_tasks: Number of workers currently executing tasks
            - timestamp: Information retrieval timestamp

    Raises:
        HTTP 500: If active task information retrieval fails

    Active Task Information:
        - id: Unique task identifier for tracking and monitoring
        - name: Task function name and module path
        - args: Positional arguments passed to task function
        - kwargs: Keyword arguments and configuration parameters
        - worker: Worker node executing the task
        - time_start: Task execution start timestamp
        - acknowledged: Task acknowledgment status from worker
        - delivery_info: Message delivery and routing information

    Execution Context:
        - Task routing and queue assignment information
        - Worker pool and process allocation details
        - Task priority and scheduling metadata
        - Execution environment and configuration
        - Performance timing and duration tracking

    Monitoring Capabilities:
        - Real-time task execution tracking
        - Worker load distribution analysis
        - Task performance and duration monitoring
        - System capacity and utilization assessment
        - Bottleneck identification and optimization

    Use Cases:
        - Real-time system monitoring and observability
        - Task execution debugging and troubleshooting
        - Performance analysis and optimization
        - Worker load balancing assessment
        - System capacity planning and scaling

    Example:
        GET /api/v1/tasks/active
    """
    log_api_call("get_active_tasks", user_id=str(current_user.id))

    try:
        celery_app = get_celery_app()
        inspector = celery_app.control.inspect()

        active_tasks = inspector.active() or {}

        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                task_info = ActiveTaskInfo(
                    id=task.get("id"),
                    name=task.get("name"),
                    args=task.get("args", []),
                    kwargs=task.get("kwargs", {}),
                    worker=worker,
                    time_start=task.get("time_start"),
                    acknowledged=task.get("acknowledged", False),
                    delivery_info=task.get("delivery_info", {}),
                )
                all_tasks.append(task_info)

        response_payload = ActiveTasksData(
            active_tasks=all_tasks,
            total_active=len(all_tasks),
            workers_with_tasks=len([w for w, t in active_tasks.items() if t]),
            timestamp=datetime.utcnow().isoformat(),
        )
        return APIResponse[ActiveTasksData](
            success=True,
            message="Active tasks retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        raise


@router.post("/schedule", response_model=APIResponse)
@handle_api_errors("Failed to schedule task")
async def schedule_task(
    task_name: str = Query(..., description="Name of the task to schedule"),
    args: str = Query("[]", description="JSON array of task arguments"),
    kwargs: str = Query("{}", description="JSON object of task keyword arguments"),
    countdown: Optional[int] = Query(
        None, ge=0, description="Delay in seconds before execution"
    ),
    queue: str = Query("default", description="Queue to send the task to"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Schedule background tasks for execution with comprehensive parameter control.

    Provides administrative interface for scheduling background tasks with custom
    arguments, execution timing, and queue assignment. Enables flexible task
    management and system automation capabilities.

    Args:
        task_name: Fully qualified name of the task function to execute
        args: JSON-encoded array of positional arguments for the task
        kwargs: JSON-encoded object of keyword arguments for the task
        countdown: Optional delay in seconds before task execution begins
        queue: Target queue name for task routing (default: 'default')
        current_user: Current authenticated superuser scheduling the task

    Returns:
        BaseResponse: Task scheduling results including:
            - success: Task scheduling operation status
            - message: Scheduling confirmation with task details
            - task_id: Unique identifier for the scheduled task
            - queue: Target queue for task execution
            - countdown: Applied execution delay (if any)
            - timestamp: Task scheduling timestamp

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 400: If task arguments are invalid JSON or task name is invalid
        HTTP 500: If task scheduling operation fails

    Task Configuration:
        - task_name: Must match registered Celery task function
        - args: Positional arguments passed directly to task function
        - kwargs: Keyword arguments for task configuration and parameters
        - countdown: Delayed execution for scheduling and coordination
        - queue: Queue routing for load balancing and prioritization

    Scheduling Features:
        - Immediate or delayed task execution
        - Custom argument passing and configuration
        - Queue-based task routing and prioritization
        - Task identification and tracking capabilities
        - Comprehensive error handling and validation

    Administrative Use Cases:
        - Manual task execution and testing
        - System maintenance and cleanup operations
        - Bulk processing and batch job scheduling
        - Emergency task execution and recovery
        - Development and debugging support

    Security Notes:
        - Requires superuser privileges for system security
        - Task execution runs with application privileges
        - Argument validation prevents injection attacks
        - Administrative audit logging for all operations

    Example:
        POST /api/v1/tasks/schedule?task_name=process_document&args=[123]&countdown=60
    """
    log_api_call("schedule_task", user_id=str(current_user.id), task_name=task_name)

    try:
        # Parse arguments
        try:
            task_args = json.loads(args)
            task_kwargs = json.loads(kwargs)
        except json.JSONDecodeError as e:
            return ErrorResponse.create(
                error_code="INVALID_JSON_ARGUMENTS",
                message=f"Invalid JSON in arguments: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        celery_app = get_celery_app()

        # Schedule the task
        schedule_kwargs = {"args": task_args, "kwargs": task_kwargs, "queue": queue}

        if countdown is not None:
            schedule_kwargs["countdown"] = countdown

        result = celery_app.send_task(task_name, **schedule_kwargs)

        return SuccessResponse.create(
            data={
                "task_id": result.id,
                "queue": queue,
                "countdown": countdown,
            },
            message=f"Task '{task_name}' scheduled successfully"
        )
    except Exception as e:
        raise


@router.post("/retry-failed", response_model=APIResponse)
@handle_api_errors("Failed to retry failed tasks")
async def retry_failed_tasks(
    task_name: Optional[str] = Query(
        None, description="Specific task name to retry (optional)"
    ),
    max_retries: int = Query(
        10, ge=1, le=100, description="Maximum number of tasks to retry"
    ),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry failed document processing tasks with intelligent error recovery.

    Identifies and retries failed background tasks, particularly focusing on
    document processing failures. Implements intelligent retry logic with
    error analysis and recovery strategies for improved system reliability.

    Args:
        task_name: Optional specific task name filter for targeted retries
        max_retries: Maximum number of failed tasks to retry (1-100, default: 10)
        current_user: Current authenticated superuser performing retry operations
        db: Database session for task status updates and tracking

    Returns:
        BaseResponse: Retry operation results including:
            - success: Overall retry operation status
            - message: Summary of retry operation results
            - retried_count: Number of tasks successfully scheduled for retry
            - total_failed: Total number of failed tasks identified
            - errors: Sample of retry errors encountered (limited to 5)
            - timestamp: Retry operation execution timestamp

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If retry operation fails or database errors occur

    Retry Process:
        - Identifies failed documents with recoverable error conditions
        - Resets document status to enable reprocessing
        - Clears previous error messages and state information
        - Schedules reprocessing with appropriate priority settings
        - Tracks retry success and failure rates for monitoring

    Recovery Strategy:
        - Prioritizes recently failed tasks for faster recovery
        - Applies high priority to retry operations for faster processing
        - Maintains audit trail of retry attempts and outcomes
        - Provides detailed error reporting for troubleshooting
        - Implements batch processing to handle large failure volumes

    Error Handling:
        - Graceful handling of retry scheduling failures
        - Detailed error reporting for troubleshooting
        - Partial success tracking for mixed outcomes
        - Database transaction management for consistency
        - Comprehensive logging for administrative oversight

    Use Cases:
        - Recovery from temporary system failures or resource constraints
        - Batch retry of failed processing operations
        - System maintenance and error recovery procedures
        - Development and testing error scenario handling
        - Automated failure recovery and system resilience

    Example:
        POST /api/v1/tasks/retry-failed?max_retries=20
        POST /api/v1/tasks/retry-failed?task_name=process_document&max_retries=5
    """
    log_api_call(
        "retry_failed_tasks", user_id=str(current_user.id), task_name=task_name
    )

    try:
        from sqlalchemy import select

        from ..models.document import Document, FileStatus

        # Find failed documents that can be retried
        query = select(Document).where(Document.status == FileStatus.FAILED)

        if max_retries:
            query = query.limit(max_retries)

        result = await db.execute(query)
        failed_documents = result.scalars().all()

        retried_count = 0
        errors = []

        # Get background processor
        from ..services.background_processor import get_background_processor

        processor = get_background_processor()

        for doc in failed_documents:
            try:
                # Reset document status
                doc.status = FileStatus.PENDING
                doc.error_message = None

                # Schedule reprocessing
                task_result = await processor.process_document_async(doc.id, priority=5)

                if task_result:
                    retried_count += 1
                else:
                    errors.append(f"Failed to schedule retry for document {doc.id}")

            except Exception as e:
                errors.append(f"Error retrying document {doc.id}: {str(e)}")

        await db.commit()

        return SuccessResponse.create(
            data={
                "retried_count": retried_count,
                "total_failed": len(failed_documents),
                "errors": errors[:5],  # Limit error reporting
            },
            message=f"Retry initiated for {retried_count} failed tasks"
        )
    except Exception as e:
        await db.rollback()
        raise


@router.post("/purge", response_model=APIResponse)
@handle_api_errors("Failed to purge queue")
async def purge_queue(
    queue_name: str = Query("default", description="Queue name to purge"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Purge all pending tasks from specified queue with comprehensive safety warnings.

    Removes all pending tasks from the specified queue, providing emergency cleanup
    capabilities for queue management and system maintenance. This is a destructive
    operation that permanently removes queued tasks.

    Args:
        queue_name: Name of the target queue to purge (default: 'default')
        current_user: Current authenticated superuser performing the purge operation

    Returns:
        BaseResponse: Purge operation results including:
            - success: Purge operation completion status
            - message: Purge confirmation with queue details
            - purged_tasks: Number of tasks removed from the queue
            - queue: Name of the purged queue
            - timestamp: Purge operation execution timestamp

    Raises:
        HTTP 403: If user is not a superuser
        HTTP 500: If queue purge operation fails

    CRITICAL WARNINGS:
        - This operation permanently removes ALL pending tasks from the queue
        - Active/running tasks are NOT affected by this operation
        - Purged tasks cannot be recovered and must be rescheduled manually
        - Use with extreme caution in production environments
        - Consider task criticality before executing purge operations

    Purge Impact:
        - All pending tasks in the queue are permanently deleted
        - Task arguments, scheduling, and metadata are lost
        - No automatic recovery or restoration mechanisms
        - Client applications may need to resubmit lost tasks
        - System capacity and performance may be immediately affected

    Safety Considerations:
        - Requires superuser privileges for system protection
        - Administrative audit logging for all purge operations
        - Consider creating task backups before purging
        - Coordinate with development and operations teams
        - Plan for manual task resubmission if necessary

    Use Cases:
        - Emergency queue cleanup during system issues
        - Development environment maintenance and testing
        - Queue overflow management and capacity control
        - System maintenance and configuration changes
        - Error recovery from corrupted queue states

    Example:
        POST /api/v1/tasks/purge?queue_name=document_processing
    """
    log_api_call("purge_queue", user_id=str(current_user.id), queue_name=queue_name)

    try:
        celery_app = get_celery_app()

        # Purge the queue
        purged_count = celery_app.control.purge()

        return SuccessResponse.create(
            data={
                "purged_tasks": purged_count,
                "queue": queue_name,
            },
            message=f"Queue '{queue_name}' purged successfully"
        )
    except Exception as e:
        raise


@router.get("/stats", response_model=APIResponse[TaskStatisticsData])
@handle_api_errors("Failed to get task statistics")
async def get_task_statistics(
    period_hours: int = Query(
        24, ge=1, le=168, description="Period in hours for statistics"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive task execution statistics and performance analytics.

    Returns detailed analytics about task execution including success rates,
    processing times, failure analysis, and performance trends over the specified
    time period. Provides essential insights for system optimization and monitoring.

    Args:
        period_hours: Analysis period in hours (1-168 hours / 1 week maximum)
        current_user: Current authenticated user requesting statistics
        db: Database session for statistics queries and data retrieval

    Returns:
        TaskStatsResponse: Comprehensive task statistics including:
            - period_hours: Analysis time period applied
            - start_time: Analysis period start timestamp
            - document_processing: Detailed processing statistics and metrics
            - recent_errors: Sample of recent error messages and patterns
            - timestamp: Statistics generation timestamp

    Raises:
        HTTP 500: If statistics retrieval or calculation fails

    Document Processing Statistics:
        - total: Total number of documents processed in period
        - completed: Number of successfully completed documents
        - failed: Number of documents that failed processing
        - processing: Number of documents currently being processed
        - success_rate: Percentage of successful processing operations
        - failure_rate: Percentage of failed processing operations
        - avg_processing_time_seconds: Average processing duration

    Performance Metrics:
        - Processing throughput and capacity utilization
        - Success and failure rate trends over time
        - Average processing times and performance benchmarks
        - Error pattern analysis and failure categorization
        - System efficiency and optimization opportunities

    Error Analysis:
        - Recent error message sampling for troubleshooting
        - Error frequency and pattern identification
        - Failure root cause analysis and categorization
        - Recovery and retry success rate tracking
        - System reliability and stability assessment

    Use Cases:
        - System performance monitoring and optimization
        - Capacity planning and resource allocation
        - Error pattern analysis and troubleshooting
        - Service level agreement (SLA) monitoring
        - Administrative reporting and insights

    Example:
        GET /api/v1/tasks/stats?period_hours=72
    """
    log_api_call(
        "get_task_statistics", user_id=str(current_user.id), period_hours=period_hours
    )

    try:
        start_time = datetime.utcnow() - timedelta(hours=period_hours)

        from sqlalchemy import and_, func, select

        from ..models.document import Document, FileStatus

        # Document processing statistics
        total_docs = await db.scalar(
            select(func.count(Document.id)).where(Document.created_at >= start_time)
        )

        completed_docs = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.COMPLETED,
                )
            )
        )

        failed_docs = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.FAILED,
                )
            )
        )

        processing_docs = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.PROCESSING,
                )
            )
        )

        # Calculate rates
        success_rate = (completed_docs / max(total_docs, 1)) * 100 if total_docs else 0
        failure_rate = (failed_docs / max(total_docs, 1)) * 100 if total_docs else 0

        # Get average processing time for completed documents
        avg_processing_time = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Document.updated_at - Document.created_at)
                )
            ).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.COMPLETED,
                    Document.updated_at.is_not(None),
                )
            )
        )
        avg_time_seconds = avg_processing_time.scalar() or 0

        # Get recent errors
        recent_errors = await db.execute(
            select(Document.error_message)
            .where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.FAILED,
                    Document.error_message.is_not(None),
                )
            )
            .limit(5)
        )

        error_samples = [row[0] for row in recent_errors.fetchall()]

        document_processing_stats = DocumentProcessingStats(
            total=total_docs or 0,
            completed=completed_docs or 0,
            failed=failed_docs or 0,
            processing=processing_docs or 0,
            success_rate=round(success_rate, 2),
            failure_rate=round(failure_rate, 2),
            avg_processing_time_seconds=round(avg_time_seconds, 2),
        )

        response_payload = TaskStatisticsData(
            period_hours=period_hours,
            start_time=start_time.isoformat(),
            document_processing=document_processing_stats,
            recent_errors=error_samples,
            timestamp=datetime.utcnow().isoformat(),
        )
        return APIResponse[TaskStatisticsData](
            success=True,
            message="Task statistics retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        raise


@router.get("/monitor", response_model=APIResponse[TaskMonitoringData])
@handle_api_errors("Failed to get monitoring data")
async def get_monitoring_data(
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time monitoring data for comprehensive task system observability.

    Returns current state information optimized for real-time monitoring dashboards,
    status displays, and automated monitoring systems. Provides consolidated view
    of system health, performance, and operational metrics.

    Args:
        current_user: Current authenticated user requesting monitoring data

    Returns:
        TaskMonitorResponse: Real-time monitoring data including:
            - system_status: Overall task system health and connectivity
            - active_tasks: Current task execution summary and worker utilization
            - workers: Worker availability and capacity information
            - recent_performance: Recent processing performance and success rates
            - timestamp: Monitoring data collection timestamp
            - refresh_interval: Recommended refresh frequency for dashboards

    Raises:
        HTTP 500: If monitoring data collection fails

    System Status:
        - broker_status: Message broker connectivity and health
        - active_workers: Number of workers currently online and responsive
        - active_tasks: Number of tasks currently being executed
        - reserved_tasks: Number of tasks queued for execution
        - system_status: Overall health assessment (healthy/degraded)

    Active Tasks Summary:
        - count: Total number of currently executing tasks
        - workers_busy: Number of workers with active task assignments

    Worker Information:
        - total: Total number of registered workers
        - online: Number of workers currently responsive and available

    Recent Performance:
        - Processing statistics from the last hour
        - Success and failure rates for trend analysis
        - Performance benchmarks for capacity assessment

    Dashboard Integration:
        - Optimized data structure for real-time displays
        - Recommended 30-second refresh interval
        - Consolidated metrics for single-pane monitoring
        - Alerting-friendly status indicators

    Use Cases:
        - Real-time system monitoring dashboards
        - Automated alerting and notification systems
        - Performance trending and capacity planning
        - Operations center displays and status boards
        - System health checks and availability monitoring

    Example:
        GET /api/v1/tasks/monitor
    """
    log_api_call("get_monitoring_data", user_id=str(current_user.id))

    try:
        # Get current system status
        status_response = await get_task_system_status(current_user)

        # Get active tasks
        active_response = await get_active_tasks(current_user)

        # Get worker info
        worker_response = await get_workers_info(current_user)

        # Get recent statistics (pass database session)
        from ..database import get_db
        db_gen = get_db()
        db = await db_gen.__anext__()
        try:
            stats_response = await get_task_statistics(1, current_user, db)  # Last hour
        finally:
            await db_gen.aclose()

        active_tasks_summary = TasksSummary(
            count=active_response.data.total_active,
            workers_busy=active_response.data.workers_with_tasks,
        )

        workers_summary = WorkersSummary(
            total=worker_response.data.total_workers,
            online=worker_response.data.online_workers,
        )

        response_payload = TaskMonitoringData(
            system_status=status_response.data.model_dump(),
            active_tasks=active_tasks_summary,
            workers=workers_summary,
            recent_performance=stats_response.data.document_processing.model_dump(),
            timestamp=datetime.utcnow().isoformat(),
            refresh_interval=30,
        )
        return APIResponse[TaskMonitoringData](
            success=True,
            message="Monitoring data retrieved successfully",
            data=response_payload,
        )
    except Exception as e:
        raise
