"""Unified logging service for the AI Chatbot Platform with comprehensive observability and monitoring.

This module provides a centralized, standardized logging system that consolidates all
logging functionality into a single service with advanced features for production
monitoring, debugging, and performance analysis with structured logging support.
"""

import json
import logging
import logging.handlers
import sys
import time
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from app.config import settings


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging.

    Provides consistent structured logging with metadata for monitoring
    and log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry - use timezone-aware datetime
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        # Add user ID if available
        user_id = getattr(record, "user_id", None)
        if user_id:
            log_entry["user_id"] = user_id

        # Add operation context if available
        operation = getattr(record, "operation", None)
        if operation:
            log_entry["operation"] = operation

        # Add performance metrics if available
        duration = getattr(record, "duration", None)
        if duration is not None:
            log_entry["duration_ms"] = round(duration * 1000, 2)

        # Add extra fields
        extra_fields = getattr(record, "extra_fields", {})
        if extra_fields:
            log_entry.update(extra_fields)

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development logging.

    Provides colored, readable output for local development with
    essential context information.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for development readability."""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, "")
        colored_level = f"{level_color}{record.levelname}{self.RESET}"

        # Base format - use timezone-aware datetime
        timestamp = datetime.fromtimestamp(record.created, UTC).strftime("%H:%M:%S")
        base_format = (
            f"{timestamp} {colored_level:<15} {record.name:<20} {record.getMessage()}"
        )

        # Add correlation ID if available
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            base_format += f" [correlation_id={correlation_id}]"

        # Add operation context if available
        operation = getattr(record, "operation", None)
        if operation:
            base_format += f" [operation={operation}]"

        # Add duration if available
        duration = getattr(record, "duration", None)
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
    """Filter to add contextual information to log records.

    Adds correlation IDs, user context, and operation context to all log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        # Add correlation ID if not present
        if not hasattr(record, "correlation_id"):
            record.correlation_id = getattr(self, "_correlation_id", None)

        # Add user ID if not present
        if not hasattr(record, "user_id"):
            record.user_id = getattr(self, "_user_id", None)

        # Add operation if not present
        if not hasattr(record, "operation"):
            record.operation = getattr(self, "_operation", None)

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
    """Logger for performance monitoring and metrics.

    Provides easy-to-use decorators and context managers for
    tracking operation performance.
    """

    def __init__(self, logger: logging.Logger):
        """Initialize PerformanceLogger with a logger instance."""
        self.logger = logger

    def log_operation(
        self, operation: str, duration: float, success: bool = True, **kwargs
    ):
        """Log an operation with performance metrics.

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
            **kwargs,
        }

        if success:
            self.logger.info(
                f"Operation completed: {operation}",
                extra={"extra_fields": extra_fields},
            )
        else:
            self.logger.error(
                f"Operation failed: {operation}", extra={"extra_fields": extra_fields}
            )

    def time_operation(self, operation: str, **context):
        """Context manager for timing operations.

        Args:
            operation: Operation name
            **context: Additional context

        """
        return OperationTimer(self, operation, **context)


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, perf_logger: PerformanceLogger, operation: str, **context):
        """Initialize OperationTimer with performance logger and operation details."""
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
            self.operation, duration, self.success, **self.context
        )

        return False  # Don't suppress exceptions


class StructuredLogger:
    """Structured logger for consistent log formatting.

    This class provides methods for logging with structured data
    that can be easily parsed and analyzed. It also includes timing
    capabilities and contextual information for better observability.

    This is provided for backward compatibility with existing services.
    """

    def __init__(self, name: str):
        """Initialize structured logger.

        Args:
            name: Logger name (typically module or service name)

        """
        self.logger = logging.getLogger(name)
        self.name = name

    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self._log_with_context("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self._log_with_context("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self._log_with_context("error", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self._log_with_context("debug", message, **kwargs)

    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with consistent formatting.

        Args:
            level: Log level (info, warning, error, debug)
            message: Primary log message
            **kwargs: Additional structured data

        """
        log_method = getattr(self.logger, level)

        if kwargs:
            log_method(message, extra={"extra_fields": kwargs})
        else:
            log_method(message)

    def log_operation(self, operation: str, status: str = "started", **kwargs):
        """Log service operations with consistent format.

        Args:
            operation: Name of the operation
            status: Status of operation (started, completed, failed)
            **kwargs: Additional context

        """
        level = "info" if status != "failed" else "error"
        self._log_with_context(
            level,
            f"Operation {operation} {status}",
            operation=operation,
            status=status,
            service=self.name,
            **kwargs,
        )

    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics for operations.

        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            **kwargs: Additional context

        """
        self.info(
            f"Performance metric for {operation}",
            operation=operation,
            duration_ms=duration_ms,
            performance_type="timing",
            service=self.name,
            **kwargs,
        )


class LoggingService:
    """Centralized logging service for the application.

    This class provides a unified interface for all logging functionality,
    consolidating configuration, context management, and specialized loggers.
    """

    def __init__(self):
        """Initialize LoggingService with default configuration."""
        self._context_filter = None
        self._initialized = False

    def setup_logging(
        self,
        log_level: Optional[str] = None,
        log_format: Optional[str] = None,
        log_file: Optional[str] = None,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """Set up standardized logging for the application.

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
        log_level = log_level or getattr(settings, "log_level", "INFO")
        log_format = log_format or (
            "structured" if not getattr(settings, "debug", False) else "development"
        )

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Choose formatter
        if log_format == "structured":
            formatter = StructuredFormatter()
        else:
            formatter = DevelopmentFormatter()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)

        # Add context filter
        self._context_filter = ContextFilter()
        console_handler.addFilter(self._context_filter)

        root_logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(
                StructuredFormatter()
            )  # Always use structured format for files
            file_handler.addFilter(self._context_filter)

            root_logger.addHandler(file_handler)

        # Set up third-party library logging levels
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        self._initialized = True
        return root_logger

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with standardized configuration.

        Args:
            name: Logger name (usually __name__)

        Returns:
            logging.Logger: Configured logger instance

        """
        return logging.getLogger(name)

    def get_api_logger(self, endpoint_name: str) -> logging.Logger:
        """Get a standardized logger for API endpoints.

        Args:
            endpoint_name: Name of the API endpoint

        Returns:
            logging.Logger: Configured logger instance

        """
        return self.get_logger(f"api.{endpoint_name.lower()}")

    def get_service_logger(self, service_name: str) -> logging.Logger:
        """Get a standardized logger for service classes.

        Args:
            service_name: Name of the service (typically class name)

        Returns:
            logging.Logger: Configured logger instance

        """
        return self.get_logger(f"service.{service_name.lower()}")

    def get_component_logger(self, component_name: str) -> logging.Logger:
        """Get a standardized logger for application components.

        Args:
            component_name: Name of the component

        Returns:
            logging.Logger: Configured logger instance

        """
        return self.get_logger(f"component.{component_name.lower()}")

    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """Get a performance logger for metrics tracking.

        Args:
            name: Logger name

        Returns:
            PerformanceLogger: Performance logger instance

        """
        logger = self.get_logger(name)
        return PerformanceLogger(logger)

    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """Set correlation ID for the current context.

        Args:
            correlation_id: Optional correlation ID, generates one if None

        Returns:
            str: The correlation ID that was set

        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        if self._context_filter:
            self._context_filter.set_correlation_id(correlation_id)

        return correlation_id

    def set_user_context(self, user_id: str):
        """Set user context for logging.

        Args:
            user_id: User ID to associate with log entries

        """
        if self._context_filter:
            self._context_filter.set_user_id(user_id)

    def set_operation_context(self, operation: str):
        """Set operation context for logging.

        Args:
            operation: Operation name to associate with log entries

        """
        if self._context_filter:
            self._context_filter.set_operation(operation)

    def log_structured(
        self, logger: logging.Logger, level: str, message: str, **kwargs
    ):
        """Log a message with structured data.

        Args:
            logger: Logger instance to use
            level: Log level (info, warning, error, debug)
            message: Primary log message
            **kwargs: Additional structured data

        """
        log_method = getattr(logger, level.lower())

        if kwargs:
            extra_fields = kwargs
            log_method(message, extra={"extra_fields": extra_fields})
        else:
            log_method(message)


# Global logging service instance
logging_service = LoggingService()


# Convenience functions for backward compatibility
def setup_logging(**kwargs) -> logging.Logger:
    """Set up logging using the global logging service."""
    return logging_service.setup_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """Get a logger using the global logging service."""
    return logging_service.get_logger(name)


def get_api_logger(endpoint_name: str) -> logging.Logger:
    """Get an API logger using the global logging service."""
    return logging_service.get_api_logger(endpoint_name)


def get_service_logger(service_name: str) -> logging.Logger:
    """Get a service logger using the global logging service."""
    return logging_service.get_service_logger(service_name)


def get_component_logger(component_name: str) -> logging.Logger:
    """Get a component logger using the global logging service."""
    return logging_service.get_component_logger(component_name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger using the global logging service."""
    return logging_service.get_performance_logger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID using the global logging service."""
    return logging_service.set_correlation_id(correlation_id)


def set_user_context(user_id: str):
    """Set user context using the global logging service."""
    logging_service.set_user_context(user_id)


def set_operation_context(operation: str):
    """Set operation context using the global logging service."""
    logging_service.set_operation_context(operation)


# Export StructuredLogger for backward compatibility
__all__ = [
    "LoggingService",
    "StructuredLogger",
    "PerformanceLogger",
    "OperationTimer",
    "setup_logging",
    "get_logger",
    "get_api_logger",
    "get_service_logger",
    "get_component_logger",
    "get_performance_logger",
    "set_correlation_id",
    "set_user_context",
    "set_operation_context",
]
