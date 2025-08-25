"""Job model for scheduled and recurring tasks.

This module defines the Job model for managing scheduled and recurring tasks
in the AI Chatbot Platform. Jobs represent higher-level recurring operations
that can create background tasks at scheduled intervals.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModelDB


class JobStatus(str, Enum):
    """Job status enumeration."""
    
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILED = "failed"


class JobType(str, Enum):
    """Job type enumeration."""
    
    DOCUMENT_CLEANUP = "document_cleanup"
    ANALYTICS_AGGREGATION = "analytics_aggregation"
    USER_ACTIVITY_DIGEST = "user_activity_digest"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    DATABASE_MAINTENANCE = "database_maintenance"
    MCP_SERVER_HEALTH_CHECK = "mcp_server_health_check"
    CUSTOM = "custom"


class ScheduleType(str, Enum):
    """Schedule type enumeration."""
    
    CRON = "cron"  # Traditional cron expression
    INTERVAL = "interval"  # Simple interval in minutes
    DAILY = "daily"  # Daily at specific time
    WEEKLY = "weekly"  # Weekly on specific day/time
    MONTHLY = "monthly"  # Monthly on specific date/time


class Job(BaseModelDB):
    """Job model for scheduled and recurring tasks.
    
    Represents a scheduled job that can be executed periodically or on a schedule.
    Jobs can create background tasks when they run and track execution history.
    """
    
    __tablename__ = "jobs"
    
    # Basic job information
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    job_type: Mapped[JobType] = mapped_column(String(50), nullable=False, index=True)
    
    # Status and control
    status: Mapped[JobStatus] = mapped_column(String(20), nullable=False, default=JobStatus.ACTIVE, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Scheduling configuration
    schedule_type: Mapped[ScheduleType] = mapped_column(String(20), nullable=False)
    schedule_expression: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    
    # Execution configuration
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_args: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    task_kwargs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    task_queue: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    task_priority: Mapped[int] = mapped_column(Integer, default=5)
    timeout_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Execution tracking
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_task_id: Mapped[Optional[str]] = mapped_column(String(100))
    last_task_status: Mapped[Optional[str]] = mapped_column(String(20))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Statistics
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0)
    average_duration_seconds: Mapped[Optional[float]] = mapped_column()
    
    # Configuration and metadata
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    def __repr__(self) -> str:
        """String representation of the job."""
        return f"<Job(id={self.id}, name='{self.name}', status='{self.status}', type='{self.job_type}')>"
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100.0
    
    @property
    def is_overdue(self) -> bool:
        """Check if the job is overdue for execution."""
        if not self.next_run_at or not self.is_enabled or self.status != JobStatus.ACTIVE:
            return False
        return datetime.utcnow() > self.next_run_at.replace(tzinfo=None)
    
    def update_execution_stats(self, success: bool, duration_seconds: Optional[float] = None) -> None:
        """Update job execution statistics.
        
        Args:
            success: Whether the execution was successful
            duration_seconds: How long the execution took
        """
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
            
        if duration_seconds is not None:
            if self.average_duration_seconds is None:
                self.average_duration_seconds = duration_seconds
            else:
                # Running average
                self.average_duration_seconds = (
                    (self.average_duration_seconds * (self.total_runs - 1) + duration_seconds) 
                    / self.total_runs
                )