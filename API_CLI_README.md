# API-Based Management CLI

This is a comprehensive API-based command-line interface that provides all functionality of the original `manage.py` script, but operates through REST API endpoints instead of direct database access.

## Overview

The API CLI (`api_manage.py`) duplicates every feature of the original CLI while offering several advantages:

- **API-first architecture**: All operations go through the REST API
- **Authentication support**: Token-based authentication with persistence
- **Network-based**: Can manage remote servers
- **Consistent error handling**: Standardized API error responses
- **Enhanced features**: Additional functionality and improved UX

## Quick Start

### 1. Authentication

First, authenticate with the API server:

```bash
# Login and save token
python api_manage.py login

# Check authentication status
python api_manage.py auth-status

# Logout
python api_manage.py logout
```

### 2. System Health

Check if the system is operational:

```bash
# Comprehensive health check
python api_manage.py health

# System status overview
python api_manage.py status

# Show version information
python api_manage.py version
```

### 3. Basic Operations

```bash
# List users
python api_manage.py users list

# Upload document
python api_manage.py documents upload file.pdf

# View conversations
python api_manage.py conversations list

# System analytics
python api_manage.py analytics overview
```

## Command Structure

The CLI maintains the same command structure as the original `manage.py`:

### User Management
```bash
python api_manage.py users create john john@example.com
python api_manage.py users list --active-only
python api_manage.py users show john
python api_manage.py users reset-password john
python api_manage.py users promote john    # Make superuser
python api_manage.py users deactivate john
python api_manage.py users stats
```

### Document Management
```bash
python api_manage.py documents upload file.pdf --title "My Document"
python api_manage.py documents list --status completed
python api_manage.py documents show doc-id
python api_manage.py documents search "machine learning"
python api_manage.py documents reprocess doc-id
python api_manage.py documents cleanup --older-than 30 --dry-run
python api_manage.py documents stats
```

### Conversation Management
```bash
python api_manage.py conversations list --user john
python api_manage.py conversations show conv-id --messages
python api_manage.py conversations export conv-id --format json
python api_manage.py conversations import-conversation backup.json
python api_manage.py conversations search "API documentation"
python api_manage.py conversations archive --older-than 90 --dry-run
python api_manage.py conversations stats
```

### Analytics & Reporting
```bash
python api_manage.py analytics overview
python api_manage.py analytics usage --period 30d --detailed
python api_manage.py analytics performance
python api_manage.py analytics users --metric messages --top 10
python api_manage.py analytics trends --days 14
python api_manage.py analytics export-report --output report.json
```

### Database Management
```bash
python api_manage.py database init
python api_manage.py database status
python api_manage.py database tables
python api_manage.py database migrations
python api_manage.py database upgrade
python api_manage.py database backup --output backup.sql
python api_manage.py database vacuum
python api_manage.py database analyze
python api_manage.py database query "SELECT COUNT(*) FROM users"
```

### Background Tasks
```bash
python api_manage.py tasks status
python api_manage.py tasks workers
python api_manage.py tasks queue
python api_manage.py tasks active
python api_manage.py tasks retry-failed
python api_manage.py tasks schedule my_task --args '["arg1"]'
python api_manage.py tasks stats --period 24
python api_manage.py tasks monitor
```

### Prompt Management
```bash
python api_manage.py prompts list
python api_manage.py prompts show my-prompt
python api_manage.py prompts add my-prompt --title "My Prompt" --content "You are..."
python api_manage.py prompts update my-prompt --title "Updated Title"
python api_manage.py prompts set-default my-prompt
python api_manage.py prompts activate my-prompt
python api_manage.py prompts stats
```

### LLM Profile Management
```bash
python api_manage.py profiles list
python api_manage.py profiles show creative
python api_manage.py profiles add creative --title "Creative" --temperature 1.0
python api_manage.py profiles update creative --temperature 0.8
python api_manage.py profiles clone creative creative-v2
python api_manage.py profiles set-default balanced
python api_manage.py profiles stats
```

## Configuration

The CLI uses environment variables for configuration:

```bash
# API endpoint
export API_BASE_URL=http://localhost:8000

# Request timeout
export API_TIMEOUT=30

# Load from .env file
python api_manage.py config
```

## Advanced Features

### Enhanced Error Handling
- Comprehensive error messages with context
- API-specific error codes and details
- Graceful handling of network issues

### Improved Output
- Rich formatted tables and panels
- Color-coded status indicators  
- Progress indicators for long operations

### Batch Operations
- Document cleanup with preview mode
- Conversation archival with filtering
- Bulk user management operations

### Export/Import
- Conversation export in multiple formats (JSON, TXT, CSV)
- Analytics report export
- Database backup operations

### Real-time Monitoring
- Task system monitoring
- Performance metrics tracking
- System health indicators

## API Endpoints

The CLI utilizes these API endpoint categories:

### Core APIs
- `/api/v1/auth/*` - Authentication
- `/api/v1/users/*` - User management
- `/api/v1/documents/*` - Document management
- `/api/v1/conversations/*` - Conversation management
- `/api/v1/search/*` - Search operations
- `/api/v1/health/*` - Health checks

### Management APIs
- `/api/v1/admin/users/*` - Advanced user operations
- `/api/v1/admin/documents/*` - Document administration
- `/api/v1/admin/conversations/*` - Conversation administration
- `/api/v1/analytics/*` - Analytics and reporting
- `/api/v1/database/*` - Database management
- `/api/v1/tasks/*` - Background task management

### Registry APIs
- `/api/v1/prompts/*` - Prompt management
- `/api/v1/profiles/*` - LLM profile management
- `/api/v1/tools/*` - MCP tool management

## Testing

The CLI includes a comprehensive test suite:

```bash
# Run all tests
python test_api_cli.py

# View test help
python test_api_cli.py --help
```

The test suite verifies:
- Command structure and parsing
- Help system functionality
- Error handling
- Authentication flow
- All major command categories

## Migration from Original CLI

The API CLI is designed to be a drop-in replacement:

1. **Same command structure**: All commands use identical syntax
2. **Compatible options**: All command-line options are preserved
3. **Enhanced functionality**: Additional features and better error handling
4. **API-based**: Operations go through REST API instead of direct DB access

### Migration Steps

1. Ensure API server is running
2. Authenticate with API CLI: `python api_manage.py login`
3. Replace `python manage.py` with `python api_manage.py` in scripts
4. Verify operations work as expected

### Differences from Original

- **Authentication required**: Must login to API before operations
- **Network dependency**: Requires running API server
- **Enhanced output**: Better formatted results and error messages
- **Additional features**: New commands for advanced operations

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check auth status
python api_manage.py auth-status

# Re-authenticate
python api_manage.py logout
python api_manage.py login
```

**Connection Issues**
```bash
# Check API server
python api_manage.py health

# Verify configuration
python api_manage.py config
```

**Command Not Found**
```bash
# Check command help
python api_manage.py --help
python api_manage.py [module] --help
```

### Debug Mode

Set debug environment variables for troubleshooting:

```bash
export DEBUG=true
export API_TIMEOUT=60
python api_manage.py [command]
```

## Development

### Adding New Commands

1. Create or extend module in `api_cli/`
2. Add API endpoint if needed in `app/api/`
3. Update main CLI in `api_manage.py`
4. Add tests to `test_api_cli.py`

### Architecture

```
api_manage.py          # Main CLI script
api_cli/
├── __init__.py        # Module initialization
├── base.py            # Base classes and utilities
├── auth.py            # Authentication management
├── users.py           # User management commands
├── documents.py       # Document management commands
├── conversations.py   # Conversation management commands
├── analytics.py       # Analytics commands
├── database.py        # Database management commands
├── tasks.py           # Task management commands
├── prompts.py         # Prompt management commands
└── profiles.py        # Profile management commands
```

## Requirements

- Python 3.8+
- Running FastAPI server
- Required Python packages (see `requirements.txt`)
- Valid authentication credentials
- Network access to API server

## Security

- Token-based authentication
- Secure token storage in user directory
- HTTPS support for production deployments
- Role-based access control through API
- Audit logging of administrative operations