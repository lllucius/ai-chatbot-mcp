"""Background task management API endpoints."""

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.common import APIResponse, ErrorResponse, SuccessResponse
from shared.schemas.task_responses import (
    ActiveTaskInfo,
    ActiveTasksData,
    DocumentProcessingStats,
    QueueInfo,
    QueueStatusData,
    TaskInfo,
    TaskMonitoringData,
    TasksSummary,
    TaskStatisticsData,
    TaskSystemStatusData,
    WorkerInfo,
    WorkersSummary,
    WorkerStatusData,
)

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tasks"])


def get_celery_app():
    """Get Celery application instance for task management operations."""
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
) -> APIResponse[TaskSystemStatusData]:
    """Get comprehensive background task system status and health metrics."""
    log_api_call("get_task_system_status", user_id=str(current_user.id))

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
            sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
        )
    except Exception:
        total_active = 0

    # Get queue lengths
    try:
        reserved_tasks = inspector.reserved() if broker_status == "connected" else {}
        total_reserved = (
            sum(len(tasks) for tasks in reserved_tasks.values())
            if reserved_tasks
            else 0
        )
    except Exception:
        total_reserved = 0

    payload = TaskSystemStatusData(
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
        data=payload,
    )


@router.get("/workers", response_model=APIResponse[WorkerStatusData])
@handle_api_errors("Failed to get worker information")
async def get_workers_info(
    current_user: User = Depends(get_current_user),
) -> APIResponse[WorkerStatusData]:
    """Get comprehensive information about Celery workers with detailed status and metrics."""
    log_api_call("get_workers_info", user_id=str(current_user.id))

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
            status=("online" if worker_ping.get("ok") == "pong" else "offline"),
            pool=worker_stats.get("pool", {}).get("implementation", "unknown"),
            processes=worker_stats.get("pool", {}).get("processes", 0),
            max_concurrency=worker_stats.get("pool", {}).get("max-concurrency", 0),
            current_load=len(worker_stats.get("rusage", {})),
            broker_transport=worker_conf.get("broker_transport", "unknown"),
            prefetch_count=worker_conf.get("worker_prefetch_multiplier", 0),
            last_heartbeat=str(worker_stats.get("clock", "unknown")),
        )
        workers.append(worker_info)

    payload = WorkerStatusData(
        workers=workers,
        total_workers=len(workers),
        online_workers=len([w for w in workers if w.status == "online"]),
        timestamp=datetime.utcnow().isoformat(),
    )
    return APIResponse[WorkerStatusData](
        success=True,
        message="Worker information retrieved successfully",
        data=payload,
    )


@router.get("/queue", response_model=APIResponse[QueueStatusData])
@handle_api_errors("Failed to get queue information")
async def get_queue_info(
    queue_name: Optional[str] = Query(None, description="Specific queue to check"),
    current_user: User = Depends(get_current_user),
) -> APIResponse[QueueStatusData]:
    """Get comprehensive task queue information with detailed metrics and task tracking."""
    log_api_call("get_queue_info", user_id=str(current_user.id), queue_name=queue_name)

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

    payload = QueueStatusData(
        queues=queue_infos,
        total_queues=len(queues),
        filtered_by=queue_name,
        timestamp=datetime.utcnow().isoformat(),
    )
    return APIResponse[QueueStatusData](
        success=True,
        message="Queue information retrieved successfully",
        data=payload,
    )


@router.get("/active", response_model=APIResponse[ActiveTasksData])
@handle_api_errors("Failed to get active tasks")
async def get_active_tasks(
    current_user: User = Depends(get_current_user),
) -> APIResponse[ActiveTasksData]:
    """Get comprehensive information about currently executing tasks with detailed metadata."""
    log_api_call("get_active_tasks", user_id=str(current_user.id))

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

    payload = ActiveTasksData(
        active_tasks=all_tasks,
        total_active=len(all_tasks),
        workers_with_tasks=len([w for w, t in active_tasks.items() if t]),
        timestamp=datetime.utcnow().isoformat(),
    )
    return APIResponse[ActiveTasksData](
        success=True,
        message="Active tasks retrieved successfully",
        data=payload,
    )


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
    """Schedule background tasks for execution with comprehensive parameter control."""
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
                status_code=status.HTTP_400_BAD_REQUEST,
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
            message=f"Task '{task_name}' scheduled successfully",
        )
    except Exception:
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
    """Retry failed document processing tasks with intelligent error recovery."""
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
            message=f"Retry initiated for {retried_count} failed tasks",
        )
    except Exception:
        await db.rollback()
        raise


@router.post("/purge", response_model=APIResponse)
@handle_api_errors("Failed to purge queue")
async def purge_queue(
    queue_name: str = Query("default", description="Queue name to purge"),
    current_user: User = Depends(get_current_superuser),
):
    """Purge all pending tasks from specified queue with comprehensive safety warnings."""
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
            message=f"Queue '{queue_name}' purged successfully",
        )
    except Exception:
        raise


@router.get("/stats", response_model=APIResponse[TaskStatisticsData])
@handle_api_errors("Failed to get task statistics")
async def get_task_statistics(
    period_hours: int = Query(
        24, ge=1, le=168, description="Period in hours for statistics"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TaskStatisticsData]:
    """Get comprehensive task execution statistics and performance analytics."""
    log_api_call(
        "get_task_statistics", user_id=str(current_user.id), period_hours=period_hours
    )

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
            func.avg(func.extract("epoch", Document.updated_at - Document.created_at))
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

    payload = TaskStatisticsData(
        period_hours=period_hours,
        start_time=start_time.isoformat(),
        document_processing=document_processing_stats,
        recent_errors=error_samples,
        timestamp=datetime.utcnow().isoformat(),
    )
    return APIResponse[TaskStatisticsData](
        success=True,
        message="Task statistics retrieved successfully",
        data=payload,
    )


@router.get("/monitor", response_model=APIResponse[TaskMonitoringData])
@handle_api_errors("Failed to get monitoring data")
async def get_monitoring_data(
    current_user: User = Depends(get_current_user),
) -> APIResponse[TaskMonitoringData]:
    """Get real-time monitoring data for comprehensive task system observability."""
    log_api_call("get_monitoring_data", user_id=str(current_user.id))

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

    payload = TaskMonitoringData(
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
        data=payload,
    )
