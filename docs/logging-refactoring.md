# Logging Service Refactoring

## Overview

This refactoring consolidates all logging functionality from scattered locations into a unified, standardized logging service. The changes provide better organization, enhanced debugging capabilities, and maintain backward compatibility.

## What Was Refactored

### Before (Scattered Logging)
- `app/main.py` - `log_requests` middleware function
- `app/utils/logging.py` - Basic logging configuration
- `app/utils/standard_logging.py` - Advanced logging with structured output
- `app/utils/tool_middleware.py` - Tool-specific logging decorators
- Various files importing different logging utilities

### After (Unified Logging Service)
- `app/core/logging.py` - **NEW** Unified logging service
- `app/middleware/` - **NEW** Organized middleware package
  - `app/middleware/logging.py` - Request/response logging middleware
  - `app/middleware/core.py` - Core middleware components
- `app/utils/logging.py` - **DEPRECATED** Backward compatibility wrapper
- `app/utils/standard_logging.py` - **DEPRECATED** Backward compatibility wrapper

## New Features

### 1. Unified Logging Service (`app/core/logging.py`)
- **Single source of truth** for all logging configuration
- **Structured logging** with JSON output for production
- **Development-friendly** colored console output
- **Correlation IDs** for request tracing
- **Context filters** for user and operation tracking
- **Performance logging** with timing capabilities

### 2. Debug Content Logging
When `settings.debug = True`, the system logs:
- **Full request details**: headers, body, query parameters
- **Full response details**: headers, body, status codes
- **Nicely formatted JSON** for easy debugging
- **Correlation ID tracking** across request/response pairs

### 3. Organized Middleware Package
- **`app/middleware/logging.py`**: HTTP request/response logging
- **`app/middleware/core.py`**: Timing, validation, rate limiting
- **Proper middleware ordering** with clear separation of concerns

### 4. Enhanced Logging Features
- **Correlation IDs**: Automatically generated for each request
- **Structured data**: Extra fields for context and metrics
- **Multiple logger types**: API, Service, Component loggers
- **Backward compatibility**: Old imports continue to work

## Usage Examples

### Basic Logging
```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Basic log message")
```

### Structured Logging with Context
```python
from app.core.logging import get_api_logger

logger = get_api_logger("user_management")
logger.info("User action completed", extra={
    "extra_fields": {
        "user_id": "123",
        "action": "profile_update",
        "duration_ms": 250
    }
})
```

### Service Logging
```python
from app.core.logging import get_service_logger

logger = get_service_logger("DocumentService")
logger.info("Document processed", operation="embedding", status="success")
```

### Performance Logging
```python
from app.core.logging import get_performance_logger

perf_logger = get_performance_logger("api.documents")
with perf_logger.time_operation("document_upload", user_id="123"):
    # Process document upload
    pass
```

### Correlation ID Management
```python
from app.core.logging import set_correlation_id, get_logger

correlation_id = set_correlation_id()  # Auto-generates UUID
logger = get_logger(__name__)
logger.info("Processing request")  # Automatically includes correlation_id
```

## Middleware Configuration

The middleware is applied in the following order (outermost to innermost):

1. **Rate Limiting** - Prevent abuse
2. **Input Validation** - Sanitize inputs
3. **Request Timing** - Add performance headers
4. **Standard Logging** - Log all requests/responses
5. **Debug Content Logging** - Log detailed content (debug mode only)

```python
# In main.py
@app.middleware("http")
async def rate_limiting_middleware_wrapper(request: Request, call_next):
    return await rate_limiting_middleware(request, call_next)

@app.middleware("http")
async def logging_middleware_wrapper(request: Request, call_next):
    return await logging_middleware(request, call_next)

@app.middleware("http")
async def debug_content_middleware_wrapper(request: Request, call_next):
    return await debug_content_middleware(request, call_next)
```

## Debug Mode Features

When `settings.debug = True`:
- **Detailed request logging**: Headers, body, query parameters
- **Detailed response logging**: Headers, body, status codes
- **Pretty-printed JSON** in log output
- **Human-readable timestamps** and colored output
- **Full error tracebacks** with context

Example debug output:
```
19:45:23 INFO   component.middleware.logging Request started [correlation_id=abc123]
19:45:23 DEBUG  component.middleware.logging 📥 DEBUG REQUEST DETAILS [correlation_id=abc123]
19:45:23 DEBUG  component.middleware.logging 📤 DEBUG RESPONSE DETAILS [correlation_id=abc123]
19:45:23 INFO   component.middleware.logging Request completed [correlation_id=abc123]
```

## Migration Guide

### For Existing Code
No changes required! All existing imports continue to work:

```python
# These still work (backward compatibility)
from app.utils.logging import setup_logging, get_logger
from app.utils.logging import StructuredLogger

# But prefer the new imports
from app.core.logging import setup_logging, get_logger
from app.core.logging import StructuredLogger
```

### For New Code
Use the new unified imports:

```python
from app.core.logging import (
    setup_logging,
    get_logger,
    get_api_logger,
    get_service_logger,
    get_component_logger,
    set_correlation_id,
    StructuredLogger
)
```

## Benefits

1. **Single Source of Truth**: All logging configuration in one place
2. **Better Organization**: Clear separation between logging and middleware
3. **Enhanced Debugging**: Rich debug mode with request/response content
4. **Improved Observability**: Correlation IDs and structured logging
5. **Backward Compatibility**: No breaking changes for existing code
6. **Performance Monitoring**: Built-in timing and metrics capabilities
7. **Production Ready**: Structured JSON output for log aggregation

## Configuration

The logging service respects the following settings:
- `settings.debug`: Enables debug mode and content logging
- `settings.log_level`: Sets the logging level (DEBUG, INFO, WARNING, ERROR)

Debug mode automatically:
- Uses human-readable colored format for console output
- Logs detailed request/response content
- Includes full error tracebacks

Production mode automatically:
- Uses structured JSON format for log aggregation
- Filters out sensitive debug information
- Optimizes for performance and storage