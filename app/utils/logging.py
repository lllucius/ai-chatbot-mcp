"""
Logging configuration and utilities.

This module provides centralized logging configuration with support
for structured logging, file output, and different log levels.

"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from ..config import settings


def setup_logging() -> None:
    """
    Setup application logging configuration.

    Configures logging with console and file handlers,
    structured output, and appropriate log levels.
    """

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s (%(funcName)s)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "[%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": settings.log_level, "handlers": ["console"]},
    }

    # Apply the logging configuration
    try:
        logging.config.dictConfig(logging_config)

        # Test the configuration
        logger = logging.getLogger("app.logging")
        logger.info("Logging configuration applied successfully")

    except Exception as e:
        # Fallback to basic configuration
        logging.basicConfig(
            level=getattr(logging, str(settings.log_level).upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        logger = logging.getLogger("app.logging")
        logger.warning(f"Failed to configure advanced logging: {e}")
        logger.info("Using basic logging configuration")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"app.{name}")


class StructuredLogger:
    """
    Structured logger for consistent log formatting.

    This class provides methods for logging with structured data
    that can be easily parsed and analyzed. It also includes timing
    capabilities and contextual information for better observability.
    """

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically module or service name)
        """
        self.logger = get_logger(name)
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
        """
        Internal method to log with consistent formatting.

        Args:
            level: Log level (info, warning, error, debug)
            message: Primary log message
            **kwargs: Additional structured data
        """
        log_method = getattr(self.logger, level)

        if kwargs:
            # Create structured data string
            extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            formatted_message = f"{message} | {extra_data}"
        else:
            formatted_message = message

        log_method(formatted_message)

    def log_operation(self, operation: str, status: str = "started", **kwargs):
        """
        Log service operations with consistent format.

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
        """
        Log performance metrics for operations.

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


def get_service_logger(service_name: str) -> StructuredLogger:
    """
    Get a standardized logger for service classes.

    This is the recommended way to create loggers for service classes
    to ensure consistent logging patterns across the application.

    Args:
        service_name: Name of the service (typically class name)

    Returns:
        StructuredLogger: Configured logger instance
    """
    return StructuredLogger(f"service.{service_name.lower()}")


def get_api_logger(endpoint_name: str) -> StructuredLogger:
    """
    Get a standardized logger for API endpoints.

    Args:
        endpoint_name: Name of the API endpoint

    Returns:
        StructuredLogger: Configured logger instance
    """
    return StructuredLogger(f"api.{endpoint_name.lower()}")


def get_component_logger(component_name: str) -> StructuredLogger:
    """
    Get a standardized logger for application components.

    Args:
        component_name: Name of the component

    Returns:
        StructuredLogger: Configured logger instance
    """
    return StructuredLogger(f"component.{component_name.lower()}")
