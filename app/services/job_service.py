"""Job management service for scheduled and recurring tasks.

This service provides comprehensive job management functionality including CRUD operations,
scheduling, execution tracking, and statistics for the AI Chatbot Platform.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from croniter import croniter
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.job import Job
from app.services.base import BaseService
from app.utils.timestamp import utcnow
from shared.schemas.job import JobCreate, JobSearchParams, JobUpdate, JobStatus, ScheduleType


class JobService(BaseService):
    """Service for managing scheduled jobs with comprehensive CRUD and scheduling operations."""

    def __init__(self, db: AsyncSession):
        """Initialize job service with database session."""
        super().__init__(db, logger_name="job_service")

    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job with validation and next run calculation.
        
        Args:
            job_data: Job creation data
            
        Returns:
            Created job instance
            
        Raises:
            ValidationError: If job data is invalid
        """
        self._log_operation_start("create_job", job_name=job_data.name)
        
        try:
            # Validate schedule expression
            next_run = self._calculate_next_run(
                job_data.schedule_type,
                job_data.schedule_expression,
                job_data.timezone
            )
            
            # Check for duplicate name
            existing = await self.get_job_by_name(job_data.name, raise_if_not_found=False)
            if existing:
                raise ValidationError(f"Job with name '{job_data.name}' already exists")
            
            # Create job instance
            job = Job(
                **job_data.model_dump(),
                next_run_at=next_run
            )
            
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            
            self._log_operation_success("create_job", job_id=job.id, job_name=job.name)
            return job
            
        except Exception as e:
            await self.db.rollback()
            self._log_operation_error("create_job", e, job_name=job_data.name)
            raise

    async def get_job(self, job_id: int) -> Job:
        """Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job instance
            
        Raises:
            NotFoundError: If job not found
        """
        job = await self._get_by_id(Job, job_id, f"Job with ID {job_id} not found")
        return job

    async def get_job_by_name(self, name: str, raise_if_not_found: bool = True) -> Optional[Job]:
        """Get job by name.
        
        Args:
            name: Job name
            raise_if_not_found: Whether to raise error if not found
            
        Returns:
            Job instance or None
            
        Raises:
            NotFoundError: If job not found and raise_if_not_found is True
        """
        result = await self.db.execute(select(Job).where(Job.name == name))
        job = result.scalar_one_or_none()
        
        if not job and raise_if_not_found:
            raise NotFoundError(f"Job with name '{name}' not found")
        
        return job

    async def update_job(self, job_id: int, job_data: JobUpdate) -> Job:
        """Update job with validation and schedule recalculation.
        
        Args:
            job_id: Job ID
            job_data: Job update data
            
        Returns:
            Updated job instance
            
        Raises:
            NotFoundError: If job not found
            ValidationError: If update data is invalid
        """
        self._log_operation_start("update_job", job_id=job_id)
        
        try:
            job = await self.get_job(job_id)
            
            # Apply updates
            update_dict = job_data.model_dump(exclude_unset=True)
            
            # If schedule changed, recalculate next run
            if any(field in update_dict for field in ['schedule_type', 'schedule_expression', 'timezone']):
                schedule_type = update_dict.get('schedule_type', job.schedule_type)
                schedule_expression = update_dict.get('schedule_expression', job.schedule_expression)
                timezone = update_dict.get('timezone', job.timezone)
                
                next_run = self._calculate_next_run(schedule_type, schedule_expression, timezone)
                update_dict['next_run_at'] = next_run
            
            for field, value in update_dict.items():
                setattr(job, field, value)
            
            await self.db.commit()
            await self.db.refresh(job)
            
            self._log_operation_success("update_job", job_id=job.id, job_name=job.name)
            return job
            
        except Exception as e:
            await self.db.rollback()
            self._log_operation_error("update_job", e, job_id=job_id)
            raise

    async def delete_job(self, job_id: int) -> bool:
        """Delete job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If job not found
        """
        self._log_operation_start("delete_job", job_id=job_id)
        
        try:
            job = await self.get_job(job_id)
            await self._delete_entity(job)
            
            self._log_operation_success("delete_job", job_id=job_id, job_name=job.name)
            return True
            
        except Exception as e:
            self._log_operation_error("delete_job", e, job_id=job_id)
            raise

    async def list_jobs(
        self, 
        params: Optional[JobSearchParams] = None
    ) -> Tuple[List[Job], int]:
        """List jobs with filtering, searching and pagination.
        
        Args:
            params: Search and filter parameters
            
        Returns:
            Tuple of (jobs list, total count)
        """
        if params is None:
            params = JobSearchParams()
        
        self._log_operation_start("list_jobs", page=params.page, size=params.size)
        
        try:
            # Build base query
            query = select(Job)
            
            # Apply filters
            filters = []
            
            if params.status:
                filters.append(Job.status == params.status)
            
            if params.job_type:
                filters.append(Job.job_type == params.job_type)
            
            if params.is_enabled is not None:
                filters.append(Job.is_enabled == params.is_enabled)
            
            if params.is_overdue is not None:
                if params.is_overdue:
                    now = utcnow()
                    filters.append(
                        and_(
                            Job.next_run_at.is_not(None),
                            Job.next_run_at < now,
                            Job.is_enabled == True,
                            Job.status == JobStatus.ACTIVE.value
                        )
                    )
                else:
                    now = utcnow()
                    filters.append(
                        or_(
                            Job.next_run_at.is_(None),
                            Job.next_run_at >= now,
                            Job.is_enabled == False,
                            Job.status != JobStatus.ACTIVE.value
                        )
                    )
            
            # Text search
            if params.query:
                search_filter = or_(
                    Job.name.ilike(f"%{params.query}%"),
                    Job.title.ilike(f"%{params.query}%"),
                    Job.description.ilike(f"%{params.query}%")
                )
                filters.append(search_filter)
            
            # Tag filtering
            if params.tags:
                for key, value in params.tags.items():
                    filters.append(Job.tags[key].astext == str(value))
            
            if filters:
                query = query.where(and_(*filters))
            
            # Apply sorting
            sort_field = getattr(Job, params.sort_by, None)
            if sort_field is not None:
                if params.sort_order == "desc":
                    query = query.order_by(desc(sort_field))
                else:
                    query = query.order_by(sort_field)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)
            
            # Execute query
            result = await self.db.execute(query)
            jobs = result.scalars().all()
            
            self._log_operation_success("list_jobs", count=len(jobs), total=total)
            return list(jobs), total
            
        except Exception as e:
            self._log_operation_error("list_jobs", e)
            raise

    async def get_overdue_jobs(self) -> List[Job]:
        """Get all jobs that are overdue for execution.
        
        Returns:
            List of overdue jobs
        """
        now = utcnow()
        
        query = select(Job).where(
            and_(
                Job.next_run_at.is_not(None),
                Job.next_run_at <= now,
                Job.is_enabled == True,
                Job.status == JobStatus.ACTIVE.value
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_job_execution(
        self,
        job_id: int,
        task_id: str,
        task_status: str,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ) -> Job:
        """Update job execution tracking information.
        
        Args:
            job_id: Job ID
            task_id: Task ID that was executed
            task_status: Task execution status
            error_message: Error message if failed
            duration_seconds: Execution duration
            
        Returns:
            Updated job instance
        """
        job = await self.get_job(job_id)
        
        # Update execution tracking
        job.last_run_at = utcnow()
        job.last_task_id = task_id
        job.last_task_status = task_status
        job.last_error = error_message
        
        # Update statistics
        success = task_status in ['completed', 'success', 'SUCCESS']
        job.update_execution_stats(success, duration_seconds)
        
        # Calculate next run time
        job.next_run_at = self._calculate_next_run(
            job.schedule_type,
            job.schedule_expression,
            job.timezone,
            from_time=job.last_run_at
        )
        
        await self.db.commit()
        await self.db.refresh(job)
        
        return job

    async def get_job_stats(self) -> Dict[str, Any]:
        """Get comprehensive job statistics.
        
        Returns:
            Dictionary containing job statistics
        """
        self._log_operation_start("get_job_stats")
        
        try:
            # Basic counts
            total_jobs = await self.db.scalar(select(func.count(Job.id)))
            active_jobs = await self.db.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.ACTIVE.value)
            )
            paused_jobs = await self.db.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.PAUSED.value)
            )
            disabled_jobs = await self.db.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.DISABLED.value)
            )
            failed_jobs = await self.db.scalar(
                select(func.count(Job.id)).where(Job.status == JobStatus.FAILED.value)
            )
            
            # Execution statistics
            total_executions = await self.db.scalar(select(func.sum(Job.total_runs)))
            successful_executions = await self.db.scalar(select(func.sum(Job.successful_runs)))
            failed_executions = await self.db.scalar(select(func.sum(Job.failed_runs)))
            
            # Overdue jobs
            now = utcnow()
            jobs_overdue = await self.db.scalar(
                select(func.count(Job.id)).where(
                    and_(
                        Job.next_run_at.is_not(None),
                        Job.next_run_at <= now,
                        Job.is_enabled == True,
                        Job.status == JobStatus.ACTIVE.value
                    )
                )
            )
            
            # Recent executions (last 24h and 7d)
            day_ago = utcnow() - timedelta(days=1)
            week_ago = utcnow() - timedelta(days=7)
            
            executions_last_24h = await self.db.scalar(
                select(func.sum(Job.total_runs)).where(Job.last_run_at >= day_ago)
            )
            executions_last_7d = await self.db.scalar(
                select(func.sum(Job.total_runs)).where(Job.last_run_at >= week_ago)
            )
            
            # Calculate success rate
            avg_success_rate = 0.0
            if total_executions and total_executions > 0:
                avg_success_rate = (successful_executions / total_executions) * 100
            
            stats = {
                "total_jobs": total_jobs or 0,
                "active_jobs": active_jobs or 0,
                "paused_jobs": paused_jobs or 0,
                "disabled_jobs": disabled_jobs or 0,
                "failed_jobs": failed_jobs or 0,
                "total_executions": total_executions or 0,
                "successful_executions": successful_executions or 0,
                "failed_executions": failed_executions or 0,
                "average_success_rate": round(avg_success_rate, 2),
                "jobs_overdue": jobs_overdue or 0,
                "executions_last_24h": executions_last_24h or 0,
                "executions_last_7d": executions_last_7d or 0,
            }
            
            self._log_operation_success("get_job_stats", **stats)
            return stats
            
        except Exception as e:
            self._log_operation_error("get_job_stats", e)
            raise

    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        schedule_expression: str,
        timezone: str = "UTC",
        from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate next run time based on schedule configuration.
        
        Args:
            schedule_type: Type of schedule
            schedule_expression: Schedule expression
            timezone: Timezone for calculation
            from_time: Base time for calculation (defaults to now)
            
        Returns:
            Next run datetime or None if invalid
            
        Raises:
            ValidationError: If schedule is invalid
        """
        if from_time is None:
            from_time = utcnow()
        
        try:
            if schedule_type == ScheduleType.CRON:
                # Parse cron expression
                cron = croniter(schedule_expression, from_time)
                return cron.get_next(datetime)
            
            elif schedule_type == ScheduleType.INTERVAL:
                # Parse interval in minutes
                minutes = int(schedule_expression)
                return from_time + timedelta(minutes=minutes)
            
            elif schedule_type == ScheduleType.DAILY:
                # Parse time (HH:MM format)
                hour, minute = map(int, schedule_expression.split(':'))
                next_run = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= from_time:
                    next_run += timedelta(days=1)
                return next_run
            
            elif schedule_type == ScheduleType.WEEKLY:
                # Parse day and time (DOW:HH:MM format, DOW 0=Monday)
                parts = schedule_expression.split(':')
                dow, hour, minute = int(parts[0]), int(parts[1]), int(parts[2])
                
                # Calculate days until target day of week
                current_dow = from_time.weekday()  # 0=Monday
                days_ahead = dow - current_dow
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                next_run = from_time + timedelta(days=days_ahead)
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If we're on the target day but past the time, move to next week
                if days_ahead == 0 and next_run <= from_time:
                    next_run += timedelta(days=7)
                
                return next_run
            
            elif schedule_type == ScheduleType.MONTHLY:
                # Parse day and time (DD:HH:MM format)
                parts = schedule_expression.split(':')
                day, hour, minute = int(parts[0]), int(parts[1]), int(parts[2])
                
                # Calculate next occurrence
                next_run = from_time.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= from_time:
                    # Move to next month
                    if next_run.month == 12:
                        next_run = next_run.replace(year=next_run.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=next_run.month + 1)
                
                return next_run
            
        except Exception as e:
            raise ValidationError(f"Invalid schedule expression '{schedule_expression}' for type {schedule_type}: {e}")
        
        return None

    def validate_schedule(
        self,
        schedule_type: ScheduleType,
        schedule_expression: str,
        timezone: str = "UTC"
    ) -> Tuple[bool, Optional[str], List[datetime]]:
        """Validate schedule configuration and return next few execution times.
        
        Args:
            schedule_type: Type of schedule
            schedule_expression: Schedule expression
            timezone: Timezone for validation
            
        Returns:
            Tuple of (is_valid, error_message, next_runs)
        """
        try:
            # Calculate next few runs to validate
            next_runs = []
            current_time = utcnow()
            
            for i in range(5):  # Get next 5 runs for validation
                next_run = self._calculate_next_run(
                    schedule_type,
                    schedule_expression,
                    timezone,
                    current_time
                )
                if next_run:
                    next_runs.append(next_run)
                    current_time = next_run
                else:
                    break
            
            return True, None, next_runs
            
        except ValidationError as e:
            return False, str(e), []
        except Exception as e:
            return False, f"Unexpected error: {e}", []