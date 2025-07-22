# CLI Management System Documentation

## Overview

The AI Chatbot Platform now includes a comprehensive command-line interface (CLI) management system that provides full-featured administration capabilities for all aspects of the platform.

## Architecture

The CLI system is built with a modular architecture:

- **Single Driver Command**: `python manage.py` serves as the main entry point
- **Modular Design**: Functionality is split into separate modules:
  - `app/cli/users.py` - User management
  - `app/cli/documents.py` - Document management  
  - `app/cli/conversations.py` - Conversation management
  - `app/cli/analytics.py` - Analytics and reporting
  - `app/cli/database.py` - Database operations
  - `app/cli/tasks.py` - Background task management
- **Rich Interface**: Uses Rich library for beautiful console output
- **Type Safety**: Built with Typer for robust CLI experience

## Features

### 👥 User Management
- Create/delete users with role management
- Password reset and account activation
- User search and filtering
- Activity monitoring and statistics
- Bulk operations

### 📄 Document Management  
- Document upload and processing
- Status monitoring and reprocessing
- Semantic search capabilities
- Processing analytics
- Cleanup and maintenance operations

### 💬 Conversation Management
- Conversation listing and filtering
- Export/import in multiple formats (JSON, TXT, CSV)
- Message search across conversations
- Conversation analytics and archiving
- Chat history management

### 📊 Analytics & Reporting
- System overview and health metrics
- Usage trends and statistics
- Performance monitoring
- User activity analytics
- Comprehensive report generation

### 🗄️ Database Management
- Schema initialization and migrations
- Backup and restore operations
- Performance optimization (VACUUM, ANALYZE)
- Health checks and diagnostics
- Custom query execution

### ⚙️ Background Task Management
- Celery worker monitoring
- Task queue management
- Failed task recovery
- Performance metrics
- Real-time monitoring

## Installation

The CLI system is included with the main application. Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

Key CLI dependencies:
- `typer` - CLI framework
- `rich` - Rich console output
- `shellingham` - Shell integration

## Quick Start

1. **Initialize the system:**
   ```bash
   python manage.py database init
   python manage.py users create admin admin@example.com --superuser
   ```

2. **Check system health:**
   ```bash
   python manage.py health
   python manage.py status
   ```

3. **Get help:**
   ```bash
   python manage.py --help
   python manage.py quickstart
   python manage.py examples
   ```

## Command Structure

The CLI follows a hierarchical command structure:

```
python manage.py [MODULE] [COMMAND] [OPTIONS] [ARGUMENTS]
```

Examples:
- `python manage.py users create john john@example.com`
- `python manage.py documents list --status completed`
- `python manage.py analytics overview`

## Module Overview

### Users Module
- `create` - Create new user accounts
- `list` - List users with filtering
- `show` - Show user details
- `delete` - Delete users and data
- `reset-password` - Reset user passwords
- `activate/deactivate` - Manage user status
- `promote/demote` - Manage user roles
- `stats` - User statistics

### Documents Module
- `upload` - Upload documents for processing
- `list` - List documents with filtering
- `show` - Show document details
- `delete` - Delete documents and chunks
- `reprocess` - Reprocess failed documents
- `search` - Semantic document search
- `stats` - Document statistics
- `cleanup` - Clean up old/failed documents

### Conversations Module
- `list` - List conversations with filtering
- `show` - Show conversation details
- `export` - Export conversations to files
- `delete` - Delete conversations
- `archive` - Archive old conversations
- `search` - Search conversations and messages
- `stats` - Conversation statistics

### Analytics Module
- `overview` - System overview dashboard
- `usage` - Usage statistics by period
- `performance` - Performance metrics
- `users` - User activity analytics
- `trends` - Usage trends over time
- `export-report` - Export comprehensive reports

### Database Module
- `init` - Initialize database
- `status` - Check database status
- `tables` - List database tables
- `migrations` - Migration management
- `upgrade/downgrade` - Run migrations
- `backup/restore` - Backup operations
- `vacuum` - Optimize database
- `analyze` - Database analysis
- `query` - Execute custom queries

### Tasks Module
- `status` - Task system status
- `workers` - Worker information
- `queue` - Queue information
- `active` - Active tasks
- `schedule` - Schedule tasks
- `retry-failed` - Retry failed tasks
- `purge` - Purge task queues
- `monitor` - Real-time monitoring
- `flower` - Start Flower web interface
- `stats` - Task statistics

## Advanced Usage

### Filtering and Search
Most list commands support filtering:
```bash
python manage.py users list --active-only --search "john" --limit 10
python manage.py documents list --status completed --user alice
python manage.py conversations list --user bob --active-only
```

### Export Operations
Export data in various formats:
```bash
python manage.py conversations export 123 --format json --output backup.json
python manage.py analytics export-report --output report.csv --format csv
```

### Batch Operations
Perform bulk operations:
```bash
python manage.py documents cleanup --status failed --older-than 30
python manage.py conversations archive --older-than 90 --inactive-only
python manage.py tasks retry-failed
```

### Monitoring
Real-time monitoring capabilities:
```bash
python manage.py tasks monitor --refresh 5 --duration 300
python manage.py analytics trends --days 30
```

## Security and Safety

- Confirmation prompts for destructive operations
- `--force` flag to skip confirmations in automation
- Input validation and sanitization
- Database query limitations (SELECT only for safety)
- Proper error handling and logging

## Automation and Scripting

The CLI is designed for automation:

```bash
# Daily maintenance script
#!/bin/bash
python manage.py health
python manage.py tasks retry-failed
python manage.py database vacuum
python manage.py documents cleanup --status failed --older-than 7 --force

# Weekly backup script
#!/bin/bash
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
python manage.py database backup --output $BACKUP_FILE
python manage.py analytics export-report --output weekly_report_$(date +%Y%m%d).json
```

## Integration with Existing System

The new CLI system:
- **Preserves existing functionality** - All existing scripts remain functional
- **Extends capabilities** - Adds new features not available before
- **Maintains compatibility** - Works with existing database and models
- **Provides migration path** - Clear upgrade path from old CLI tools

## Migration from Old CLI

The old `scripts/manage.py` is deprecated but still functional:
- Shows migration notice when used
- Provides guidance to new CLI system
- All functionality available in enhanced form

To migrate:
1. Replace `python scripts/manage.py` with `python manage.py`
2. Use new module-specific commands: `python manage.py users create` instead of `python scripts/manage.py create-user`
3. Take advantage of new features like filtering, search, and export

## Error Handling

The CLI provides comprehensive error handling:
- Clear error messages with suggestions
- Graceful handling of database connection issues
- Input validation with helpful feedback
- Safe-by-default operations

## Performance Considerations

- Efficient database queries with proper indexing
- Streaming operations for large datasets
- Configurable limits and pagination
- Memory-conscious operations
- Progress indicators for long-running tasks

## Future Enhancements

Planned improvements:
- Interactive mode for guided operations
- Configuration file support
- Plugin system for custom commands
- Enhanced reporting with charts
- Integration with external monitoring systems