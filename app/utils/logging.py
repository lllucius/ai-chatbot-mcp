"""
Logging configuration and utilities.

This module provides centralized logging configuration with support
for structured logging, file output, and different log levels.

Generated on: 2025-07-14 03:10:09 UTC
Current User: lllucius
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

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
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s (%(funcName)s)",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "[%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "app": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"]
        }
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
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
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
    that can be easily parsed and analyzed.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        if kwargs:
            extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.info(f"{message} | {extra_data}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        if kwargs:
            extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.warning(f"{message} | {extra_data}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        if kwargs:
            extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.error(f"{message} | {extra_data}")
        else:
            self.logger.error(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        if kwargs:
            extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            self.logger.debug(f"{message} | {extra_data}")
        else:
            self.logger.debug(message)