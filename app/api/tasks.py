"""
Background task management API endpoints.

This module provides endpoints for managing Celery background tasks,
monitoring worker status, and controlling task execution.

Key Features:
- Task queue monitoring and management
- Worker status and health monitoring
- Task scheduling and execution control
- Failed task retry mechanisms
- Real-time task statistics
- Queue management operations

"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_superuser, get_current_user
from ..models.user import User
from ..schemas.common import BaseResponse
from ..utils.api_errors import handle_api_errors, log_api_call

router = APIRouter(tags=["tasks"])


def get_celery_app():
    """Get Celery app instance."""
    try:
        from ..core.celery_app import celery_app
        return celery_app
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Celery is not configured or available"
        )


@router.get("/status", response_model=Dict[str, Any])
@handle_api_errors("Failed to get task system status")
async def get_task_system_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get background task system status.
    
    Returns overall status of the Celery task system including
    broker connectivity, worker availability, and queue status.
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
            total_active = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
        except Exception:
            total_active = 0
        
        # Get queue lengths
        try:
            reserved_tasks = inspector.reserved() if broker_status == "connected" else {}
            total_reserved = sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0
        except Exception:
            total_reserved = 0
        
        return {
            "success": True,
            "data": {
                "broker_status": broker_status,
                "active_workers": active_workers,
                "active_tasks": total_active,
                "reserved_tasks": total_reserved,
                "system_status": "healthy" if broker_status == "connected" and active_workers > 0 else "degraded",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "broker_status": "unavailable",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }


@router.get("/workers", response_model=Dict[str, Any])
@handle_api_errors("Failed to get worker information")
async def get_workers_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get information about Celery workers.
    
    Returns detailed information about all active workers including
    their status, configuration, and current load.
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
        for worker_name in stats.keys():
            worker_stats = stats.get(worker_name, {})
            worker_ping = ping_results.get(worker_name, {})
            worker_conf = conf_results.get(worker_name, {})
            
            workers.append({
                "name": worker_name,
                "status": "online" if worker_ping.get("ok") == "pong" else "offline",
                "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                "processes": worker_stats.get("pool", {}).get("processes", 0),
                "max_concurrency": worker_stats.get("pool", {}).get("max-concurrency", 0),
                "current_load": len(worker_stats.get("rusage", {})),
                "broker_transport": worker_conf.get("broker_transport", "unknown"),
                "prefetch_count": worker_conf.get("worker_prefetch_multiplier", 0),
                "last_heartbeat": worker_stats.get("clock", "unknown")
            })
        
        return {
            "success": True,
            "data": {
                "workers": workers,
                "total_workers": len(workers),
                "online_workers": len([w for w in workers if w["status"] == "online"]),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker information: {str(e)}"
        )


@router.get("/queue", response_model=Dict[str, Any])
@handle_api_errors("Failed to get queue information")
async def get_queue_info(
    queue_name: Optional[str] = Query(None, description="Specific queue to check"),
    current_user: User = Depends(get_current_user),
):
    """
    Get task queue information.
    
    Returns information about task queues including pending tasks,
    active tasks, and queue statistics.
    
    Args:
        queue_name: Specific queue to check (optional)
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
        all_workers = set(active_tasks.keys()) | set(reserved_tasks.keys()) | set(scheduled_tasks.keys())
        
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
                        "tasks": []
                    }
                
                task_info = {
                    "id": task.get("id"),
                    "name": task.get("name"),
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "worker": worker,
                    "status": "active" if task in worker_active else "reserved" if task in worker_reserved else "scheduled"
                }
                
                queues[task_queue]["tasks"].append(task_info)
                
                if task in worker_active:
                    queues[task_queue]["active"] += 1
                elif task in worker_reserved:
                    queues[task_queue]["reserved"] += 1
                elif task in worker_scheduled:
                    queues[task_queue]["scheduled"] += 1
        
        return {
            "success": True,
            "data": {
                "queues": list(queues.values()),
                "total_queues": len(queues),
                "filtered_by": queue_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue information: {str(e)}"
        )


@router.get("/active", response_model=Dict[str, Any])
@handle_api_errors("Failed to get active tasks")
async def get_active_tasks(
    current_user: User = Depends(get_current_user),
):
    """
    Get currently active tasks.
    
    Returns detailed information about all tasks currently
    being executed by workers.
    """
    log_api_call("get_active_tasks", user_id=str(current_user.id))
    
    try:
        celery_app = get_celery_app()
        inspector = celery_app.control.inspect()
        
        active_tasks = inspector.active() or {}
        
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "id": task.get("id"),
                    "name": task.get("name"),
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "worker": worker,
                    "time_start": task.get("time_start"),
                    "acknowledged": task.get("acknowledged", False),
                    "delivery_info": task.get("delivery_info", {})
                })
        
        return {
            "success": True,
            "data": {
                "active_tasks": all_tasks,
                "total_active": len(all_tasks),
                "workers_with_tasks": len([w for w, t in active_tasks.items() if t]),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active tasks: {str(e)}"
        )


@router.post("/schedule", response_model=BaseResponse)
@handle_api_errors("Failed to schedule task")
async def schedule_task(
    task_name: str = Query(..., description="Name of the task to schedule"),
    args: str = Query("[]", description="JSON array of task arguments"),
    kwargs: str = Query("{}", description="JSON object of task keyword arguments"),
    countdown: Optional[int] = Query(None, ge=0, description="Delay in seconds before execution"),
    queue: str = Query("default", description="Queue to send the task to"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Schedule a background task for execution.
    
    Allows scheduling of background tasks with custom arguments
    and execution parameters.
    
    Args:
        task_name: Name of the task to schedule
        args: JSON array of positional arguments
        kwargs: JSON object of keyword arguments
        countdown: Delay in seconds before execution
        queue: Queue to send the task to
        
    Requires superuser access.
    """
    log_api_call("schedule_task", user_id=str(current_user.id), task_name=task_name)
    
    try:
        # Parse arguments
        try:
            task_args = json.loads(args)
            task_kwargs = json.loads(kwargs)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON in arguments: {str(e)}"
            )
        
        celery_app = get_celery_app()
        
        # Schedule the task
        schedule_kwargs = {
            "args": task_args,
            "kwargs": task_kwargs,
            "queue": queue
        }
        
        if countdown is not None:
            schedule_kwargs["countdown"] = countdown
        
        result = celery_app.send_task(task_name, **schedule_kwargs)
        
        return {
            "success": True,
            "message": f"Task '{task_name}' scheduled successfully",
            "task_id": result.id,
            "queue": queue,
            "countdown": countdown,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule task: {str(e)}"
        )


@router.post("/retry-failed", response_model=BaseResponse)
@handle_api_errors("Failed to retry failed tasks")
async def retry_failed_tasks(
    task_name: Optional[str] = Query(None, description="Specific task name to retry (optional)"),
    max_retries: int = Query(10, ge=1, le=100, description="Maximum number of tasks to retry"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry failed document processing tasks.
    
    Attempts to retry failed background tasks, particularly
    focusing on document processing failures.
    
    Args:
        task_name: Specific task name to retry (optional)
        max_retries: Maximum number of tasks to retry
        
    Requires superuser access.
    """
    log_api_call("retry_failed_tasks", user_id=str(current_user.id), task_name=task_name)
    
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
        
        return {
            "success": True,
            "message": f"Retry initiated for {retried_count} failed tasks",
            "retried_count": retried_count,
            "total_failed": len(failed_documents),
            "errors": errors[:5],  # Limit error reporting
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry tasks: {str(e)}"
        )


@router.post("/purge", response_model=BaseResponse)
@handle_api_errors("Failed to purge queue")
async def purge_queue(
    queue_name: str = Query("default", description="Queue name to purge"),
    current_user: User = Depends(get_current_superuser),
):
    """
    Purge all tasks from a queue.
    
    CAUTION: This operation will remove all pending tasks
    from the specified queue. Use with extreme care.
    
    Args:
        queue_name: Name of the queue to purge
        
    Requires superuser access.
    """
    log_api_call("purge_queue", user_id=str(current_user.id), queue_name=queue_name)
    
    try:
        celery_app = get_celery_app()
        
        # Purge the queue
        purged_count = celery_app.control.purge()
        
        return {
            "success": True,
            "message": f"Queue '{queue_name}' purged successfully",
            "purged_tasks": purged_count,
            "queue": queue_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge queue: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
@handle_api_errors("Failed to get task statistics")
async def get_task_statistics(
    period_hours: int = Query(24, ge=1, le=168, description="Period in hours for statistics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get task execution statistics.
    
    Returns statistics about task execution including success rates,
    processing times, and failure analysis.
    
    Args:
        period_hours: Period in hours to analyze (1-168 hours / 1 week max)
    """
    log_api_call("get_task_statistics", user_id=str(current_user.id), period_hours=period_hours)
    
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
                    Document.status == FileStatus.COMPLETED
                )
            )
        )
        
        failed_docs = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.FAILED
                )
            )
        )
        
        processing_docs = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.PROCESSING
                )
            )
        )
        
        # Calculate rates
        success_rate = (completed_docs / max(total_docs, 1)) * 100 if total_docs else 0
        failure_rate = (failed_docs / max(total_docs, 1)) * 100 if total_docs else 0
        
        # Get average processing time for completed documents
        avg_processing_time = await db.execute(
            select(func.avg(
                func.extract('epoch', Document.updated_at - Document.created_at)
            )).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.COMPLETED,
                    Document.updated_at.is_not(None)
                )
            )
        )
        avg_time_seconds = avg_processing_time.scalar() or 0
        
        # Get recent errors
        recent_errors = await db.execute(
            select(Document.error_message).where(
                and_(
                    Document.created_at >= start_time,
                    Document.status == FileStatus.FAILED,
                    Document.error_message.is_not(None)
                )
            ).limit(5)
        )
        
        error_samples = [row[0] for row in recent_errors.fetchall()]
        
        return {
            "success": True,
            "data": {
                "period_hours": period_hours,
                "start_time": start_time.isoformat(),
                "document_processing": {
                    "total": total_docs or 0,
                    "completed": completed_docs or 0,
                    "failed": failed_docs or 0,
                    "processing": processing_docs or 0,
                    "success_rate": round(success_rate, 2),
                    "failure_rate": round(failure_rate, 2),
                    "avg_processing_time_seconds": round(avg_time_seconds, 2)
                },
                "recent_errors": error_samples,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task statistics: {str(e)}"
        )


@router.get("/monitor", response_model=Dict[str, Any])
@handle_api_errors("Failed to get monitoring data")
async def get_monitoring_data(
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time monitoring data for task system.
    
    Returns current state information suitable for real-time
    monitoring dashboards and status displays.
    """
    log_api_call("get_monitoring_data", user_id=str(current_user.id))
    
    try:
        # Get current system status
        status_data = await get_task_system_status(current_user)
        
        # Get active tasks
        active_data = await get_active_tasks(current_user)
        
        # Get worker info
        worker_data = await get_workers_info(current_user)
        
        # Get recent statistics
        stats_data = await get_task_statistics(1, current_user, None)  # Last hour
        
        return {
            "success": True,
            "data": {
                "system_status": status_data["data"],
                "active_tasks": {
                    "count": active_data["data"]["total_active"],
                    "workers_busy": active_data["data"]["workers_with_tasks"]
                },
                "workers": {
                    "total": worker_data["data"]["total_workers"],
                    "online": worker_data["data"]["online_workers"]
                },
                "recent_performance": stats_data["data"]["document_processing"],
                "timestamp": datetime.utcnow().isoformat(),
                "refresh_interval": 30  # Suggested refresh interval in seconds
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring data: {str(e)}"
        )