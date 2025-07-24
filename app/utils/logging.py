"Utility functions for logging operations."

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict
from ..config import settings


def setup_logging() -> None:
    "Setup Logging operation."
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging_config: Dict[(str, Any)] = {
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
                "filename": str((log_dir / "app.log")),
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str((log_dir / "error.log")),
                "maxBytes": 10485760,
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
    try:
        logging.config.dictConfig(logging_config)
        logger = logging.getLogger("app.logging")
        logger.info("Logging configuration applied successfully")
    except Exception as e:
        logging.basicConfig(
            level=getattr(logging, str(settings.log_level).upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger("app.logging")
        logger.warning(f"Failed to configure advanced logging: {e}")
        logger.info("Using basic logging configuration")


def get_logger(name: str) -> logging.Logger:
    "Get logger data."
    return logging.getLogger(f"app.{name}")


class StructuredLogger:
    "StructuredLogger class for specialized functionality."

    def __init__(self, name: str):
        "Initialize class instance."
        self.logger = get_logger(name)
        self.name = name

    def info(self, message: str, **kwargs):
        "Info operation."
        self._log_with_context("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        "Warning operation."
        self._log_with_context("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        "Error operation."
        self._log_with_context("error", message, **kwargs)

    def debug(self, message: str, **kwargs):
        "Debug operation."
        self._log_with_context("debug", message, **kwargs)

    def _log_with_context(self, level: str, message: str, **kwargs):
        "Log With Context operation."
        log_method = getattr(self.logger, level)
        if kwargs:
            extra_data = " | ".join([f"{k}={v}" for (k, v) in kwargs.items()])
            formatted_message = f"{message} | {extra_data}"
        else:
            formatted_message = message
        log_method(formatted_message)

    def log_operation(self, operation: str, status: str = "started", **kwargs):
        "Log Operation operation."
        level = "info" if (status != "failed") else "error"
        self._log_with_context(
            level,
            f"Operation {operation} {status}",
            operation=operation,
            status=status,
            service=self.name,
            **kwargs,
        )

    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        "Log Performance operation."
        self.info(
            f"Performance metric for {operation}",
            operation=operation,
            duration_ms=duration_ms,
            performance_type="timing",
            service=self.name,
            **kwargs,
        )


def get_service_logger(service_name: str) -> StructuredLogger:
    "Get service logger data."
    return StructuredLogger(f"service.{service_name.lower()}")


def get_api_logger(endpoint_name: str) -> StructuredLogger:
    "Get api logger data."
    return StructuredLogger(f"api.{endpoint_name.lower()}")


def get_component_logger(component_name: str) -> StructuredLogger:
    "Get component logger data."
    return StructuredLogger(f"component.{component_name.lower()}")
