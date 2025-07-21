"""
Standardized logging configuration for the AI Chatbot Platform.

This module provides a consistent logging setup across all components of the application
with proper formatting, structured logging, and performance monitoring capabilities.

Key Features:
- Structured JSON logging for production
- Human-readable format for development
- Correlation IDs for request tracing
- Performance metrics integration
- Log level configuration
- File and console output options
- Error tracking and monitoring

Current User: assistant
Current Date: 2025-01-20
"""

import json
import logging
import logging.handlers
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from ..config import settings


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for production logging.
    
    Provides consistent structured logging with metadata for monitoring
    and log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add user ID if available
        user_id = getattr(record, 'user_id', None)
        if user_id:
            log_entry["user_id"] = user_id
            
        # Add operation context if available
        operation = getattr(record, 'operation', None)
        if operation:
            log_entry["operation"] = operation
            
        # Add performance metrics if available
        duration = getattr(record, 'duration', None)
        if duration is not None:
            log_entry["duration_ms"] = round(duration * 1000, 2)
        
        # Add extra fields
        extra_fields = getattr(record, 'extra_fields', {})
        if extra_fields:
            log_entry.update(extra_fields)
            
        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development logging.
    
    Provides colored, readable output for local development with
    essential context information.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for development readability."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        colored_level = f"{level_color}{record.levelname}{self.RESET}"
        
        # Base format
        timestamp = datetime.utcfromtimestamp(record.created).strftime("%H:%M:%S")
        base_format = f"{timestamp} {colored_level:<15} {record.name:<20} {record.getMessage()}"
        
        # Add correlation ID if available
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            base_format += f" [correlation_id={correlation_id}]"
        
        # Add operation context if available
        operation = getattr(record, 'operation', None)
        if operation:
            base_format += f" [operation={operation}]"
            
        # Add duration if available
        duration = getattr(record, 'duration', None)
        if duration is not None:
            base_format += f" [duration={duration*1000:.2f}ms]"
        
        # Add location info for debug level
        if record.levelno == logging.DEBUG:
            base_format += f" ({record.module}:{record.funcName}:{record.lineno})"
            
        # Add exception if present
        if record.exc_info:
            base_format += "\n" + "".join(traceback.format_exception(*record.exc_info))
            
        return base_format


class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records.
    
    Adds correlation IDs, user context, and operation context to all log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, '_correlation_id', None)
            
        # Add user ID if not present
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(self, '_user_id', None)
            
        # Add operation if not present
        if not hasattr(record, 'operation'):
            record.operation = getattr(self, '_operation', None)
            
        return True
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for this filter."""
        self._correlation_id = correlation_id
    
    def set_user_id(self, user_id: str):
        """Set user ID for this filter."""
        self._user_id = user_id
        
    def set_operation(self, operation: str):
        """Set operation context for this filter."""
        self._operation = operation


class PerformanceLogger:
    """
    Logger for performance monitoring and metrics.
    
    Provides easy-to-use decorators and context managers for
    tracking operation performance.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        **kwargs
    ):
        """
        Log an operation with performance metrics.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            success: Whether operation was successful
            **kwargs: Additional context
        """
        extra_fields = {
            "operation": operation,
            "duration": duration,
            "success": success,
            **kwargs
        }
        
        if success:
            self.logger.info(
                f"Operation completed: {operation}",
                extra={"extra_fields": extra_fields}
            )
        else:
            self.logger.error(
                f"Operation failed: {operation}",
                extra={"extra_fields": extra_fields}
            )
    
    def time_operation(self, operation: str, **context):
        """
        Context manager for timing operations.
        
        Args:
            operation: Operation name
            **context: Additional context
        """
        return OperationTimer(self, operation, **context)


class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, perf_logger: PerformanceLogger, operation: str, **context):
        self.perf_logger = perf_logger
        self.operation = operation
        self.context = context
        self.start_time = None
        self.success = True
        
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log results."""
        duration = time.time() - self.start_time
        self.success = exc_type is None
        
        self.perf_logger.log_operation(
            self.operation,
            duration,
            self.success,
            **self.context
        )
        
        return False  # Don't suppress exceptions


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up standardized logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('structured' for JSON, 'development' for human-readable)
        log_file: Optional log file path
        max_bytes: Maximum size for log file rotation
        backup_count: Number of backup files to keep
        
    Returns:
        logging.Logger: Configured root logger
    """
    # Determine configuration from settings
    log_level = log_level or getattr(settings, 'log_level', 'INFO')
    log_format = log_format or ('structured' if not getattr(settings, 'debug', False) else 'development')
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Choose formatter
    if log_format == 'structured':
        formatter = StructuredFormatter()
    else:
        formatter = DevelopmentFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Add context filter
    context_filter = ContextFilter()
    console_handler.addFilter(context_filter)
    
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter())  # Always use structured format for files
        file_handler.addFilter(context_filter)
        
        root_logger.addHandler(file_handler)
    
    # Set up third-party library logging levels
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with standardized configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get a performance logger for metrics tracking.
    
    Args:
        name: Logger name
        
    Returns:
        PerformanceLogger: Performance logger instance
    """
    logger = get_logger(name)
    return PerformanceLogger(logger)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.
    
    Args:
        correlation_id: Optional correlation ID, generates one if None
        
    Returns:
        str: The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    # Find context filter and set correlation ID
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_correlation_id(correlation_id)
    
    return correlation_id


def set_user_context(user_id: str):
    """
    Set user context for logging.
    
    Args:
        user_id: User ID to associate with log entries
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_user_id(user_id)


def set_operation_context(operation: str):
    """
    Set operation context for logging.
    
    Args:
        operation: Operation name to associate with log entries
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_operation(operation)


# Initialize logging on module import
_logger = setup_logging()