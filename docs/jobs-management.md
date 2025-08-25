# Jobs Management System

This document describes the complete jobs management system implementation for the AI Chatbot Platform.

## Overview

The jobs management system provides comprehensive scheduled job functionality with:

- **CRUD Operations**: Create, read, update, delete jobs
- **Cyclical Scheduling**: Support for cron expressions, intervals, daily, weekly, and monthly schedules
- **Execution Tracking**: Monitor job runs, success rates, and performance
- **REST API**: Full RESTful API with filtering and pagination
- **CLI Management**: Command-line interface for all operations
- **Default Jobs**: Pre-configured system maintenance jobs

## Job Types

The system supports several predefined job types:

- `document_cleanup`: Clean up old processed documents and temporary files
- `analytics_aggregation`: Aggregate usage statistics and generate reports
- `user_activity_digest`: Generate user activity summaries
- `system_health_check`: Monitor system health and send alerts
- `database_maintenance`: Perform database optimization tasks
- `mcp_server_health_check`: Monitor MCP server connectivity
- `custom`: User-defined job types

## Schedule Types

### Interval Schedules
```bash
# Every N minutes
schedule_type: "interval"
schedule_expression: "30"  # Every 30 minutes
```

### Daily Schedules
```bash
# Daily at specific time
schedule_type: "daily" 
schedule_expression: "14:30"  # Daily at 2:30 PM
```

### Weekly Schedules
```bash
# Weekly on specific day and time
schedule_type: "weekly"
schedule_expression: "0:09:00"  # Monday at 9:00 AM (0=Monday)
```

### Monthly Schedules
```bash
# Monthly on specific date and time
schedule_type: "monthly"
schedule_expression: "1:08:00"  # 1st day at 8:00 AM
```

### Cron Schedules
```bash
# Traditional cron expressions
schedule_type: "cron"
schedule_expression: "0 2 * * 1"  # Monday at 2:00 AM
```

## API Endpoints

### List Jobs
```http
GET /api/v1/jobs/?page=1&size=20&status=active&is_enabled=true
```

### Get Job
```http
GET /api/v1/jobs/{job_id}
```

### Create Job
```http
POST /api/v1/jobs/
Content-Type: application/json

{
  "name": "system_cleanup",
  "title": "System Cleanup Job",
  "description": "Clean up temporary files and logs",
  "job_type": "document_cleanup",
  "schedule_type": "daily",
  "schedule_expression": "02:00",
  "task_name": "app.tasks.cleanup.system_cleanup",
  "task_queue": "maintenance",
  "task_priority": 5,
  "is_enabled": true
}
```

### Update Job
```http
PUT /api/v1/jobs/{job_id}
Content-Type: application/json

{
  "schedule_expression": "03:00",
  "is_enabled": false
}
```

### Delete Job
```http
DELETE /api/v1/jobs/{job_id}
```

### Execute Job
```http
POST /api/v1/jobs/{job_id}/execute
Content-Type: application/json

{
  "force": true,
  "override_kwargs": {
    "cleanup_level": "deep"
  }
}
```

### Pause/Resume Job
```http
POST /api/v1/jobs/{job_id}/pause
POST /api/v1/jobs/{job_id}/resume
```

### Get Overdue Jobs
```http
GET /api/v1/jobs/overdue/list
```

### Get Job Statistics
```http
GET /api/v1/jobs/stats/overview
```

### Validate Schedule
```http
POST /api/v1/jobs/validate-schedule
Content-Type: application/json

{
  "schedule_type": "daily",
  "schedule_expression": "09:30",
  "timezone": "UTC"
}
```

## CLI Commands

### List Jobs
```bash
# List all jobs
./manage jobs list

# Filter by status
./manage jobs list --status active

# Filter by type
./manage jobs list --type system_health_check

# Show only enabled jobs
./manage jobs list --enabled-only

# Show only overdue jobs
./manage jobs list --overdue-only

# Pagination
./manage jobs list --page 2 --size 10
```

### Show Job Details
```bash
./manage jobs show 1
```

### Create Job
```bash
./manage jobs create \
  system_backup \
  "System Backup Job" \
  database_maintenance \
  daily \
  "03:00" \
  "app.tasks.backup.create_backup" \
  --description "Daily system backup" \
  --queue backup \
  --priority 8 \
  --timeout 7200 \
  --enabled
```

### Update Job
```bash
# Update schedule
./manage jobs update 1 --schedule "04:00"

# Update priority
./manage jobs update 1 --priority 9

# Enable/disable
./manage jobs update 1 --enabled
./manage jobs update 1 --disabled
```

### Delete Job
```bash
# With confirmation
./manage jobs delete 1

# Skip confirmation
./manage jobs delete 1 --force
```

### Execute Job
```bash
# Normal execution
./manage jobs execute 1

# Force execution (even if disabled)
./manage jobs execute 1 --force
```

### Pause/Resume Jobs
```bash
./manage jobs pause 1
./manage jobs resume 1
```

### List Overdue Jobs
```bash
./manage jobs overdue
```

### Show Statistics
```bash
./manage jobs stats
```

### Validate Schedule
```bash
# Validate interval schedule
./manage jobs validate-schedule interval 30

# Validate daily schedule
./manage jobs validate-schedule daily "09:30"

# Validate weekly schedule  
./manage jobs validate-schedule weekly "1:10:00"

# Validate with timezone
./manage jobs validate-schedule daily "14:30" --timezone "America/New_York"
```

## Default Jobs

The system creates these default jobs during initialization:

### System Health Check
- **Name**: `system_health_check`
- **Schedule**: Every 15 minutes
- **Purpose**: Monitor system components and send alerts
- **Status**: Enabled

### Document Cleanup
- **Name**: `document_cleanup`
- **Schedule**: Daily at 2:00 AM
- **Purpose**: Clean up old documents and temporary files
- **Status**: Enabled

### Analytics Aggregation
- **Name**: `analytics_aggregation`
- **Schedule**: Daily at 1:00 AM
- **Purpose**: Aggregate usage statistics and generate reports
- **Status**: Enabled

### Database Maintenance
- **Name**: `database_maintenance`
- **Schedule**: Weekly on Monday at 3:00 AM
- **Purpose**: Perform database optimization and maintenance
- **Status**: Disabled (enable manually)

### MCP Server Health Check
- **Name**: `mcp_server_health_check`
- **Schedule**: Every 30 minutes
- **Purpose**: Monitor MCP server connectivity and performance
- **Status**: Enabled

## Implementation Details

### Database Model
The `Job` model includes:
- Basic information (name, title, description, type)
- Scheduling configuration (type, expression, timezone)
- Task configuration (name, args, queue, priority)
- Execution tracking (last run, next run, task status)
- Statistics (runs, success rate, duration)
- Configuration and metadata

### Service Layer
The `JobService` provides:
- CRUD operations with validation
- Schedule calculation and validation
- Execution tracking and statistics
- Search and filtering capabilities

### Scheduling Logic
- **Interval**: Simple minute-based intervals
- **Daily**: Specific time each day
- **Weekly**: Day of week (0=Monday) and time
- **Monthly**: Day of month and time
- **Cron**: Full cron expression support

### Integration Points
- **Celery**: Background task execution
- **FastAPI**: RESTful API endpoints
- **SQLAlchemy**: Database persistence
- **Pydantic**: Schema validation
- **CLI**: Command-line management

## Error Handling

The system includes comprehensive error handling for:
- Invalid schedule expressions
- Database constraints
- Task queue connectivity
- Authentication and authorization
- Validation errors

## Security

- All endpoints require authentication
- Job creation/modification requires superuser permissions
- Input validation prevents injection attacks
- Audit logging tracks all operations

## Performance

- Efficient database queries with proper indexing
- Pagination for large result sets
- Background processing for job execution
- Caching for frequently accessed data

## Monitoring

The system provides monitoring through:
- Job execution statistics
- Success/failure rates
- Performance metrics
- Overdue job detection
- Health check integration