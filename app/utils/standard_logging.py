"Utility functions for standard_logging operations."

import json
import logging
import logging.handlers
import sys
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..config import settings


class StructuredFormatter(logging.Formatter):
    "StructuredFormatter class for specialized functionality."

    def format(self, record: logging.LogRecord) -> str:
        "Format operation."
        log_entry = {
            "timestamp": (datetime.utcfromtimestamp(record.created).isoformat() + "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        user_id = getattr(record, "user_id", None)
        if user_id:
            log_entry["user_id"] = user_id
        operation = getattr(record, "operation", None)
        if operation:
            log_entry["operation"] = operation
        duration = getattr(record, "duration", None)
        if duration is not None:
            log_entry["duration_ms"] = round((duration * 1000), 2)
        extra_fields = getattr(record, "extra_fields", {})
        if extra_fields:
            log_entry.update(extra_fields)
        if record.exc_info:
            log_entry["exception"] = {
                "type": (record.exc_info[0].__name__ if record.exc_info[0] else None),
                "message": (str(record.exc_info[1]) if record.exc_info[1] else None),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    "DevelopmentFormatter class for specialized functionality."

    COLORS = {
        "DEBUG": "\x1b[36m",
        "INFO": "\x1b[32m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[35m",
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        "Format operation."
        level_color = self.COLORS.get(record.levelname, "")
        colored_level = f"{level_color}{record.levelname}{self.RESET}"
        timestamp = datetime.utcfromtimestamp(record.created).strftime("%H:%M:%S")
        base_format = (
            f"{timestamp} {colored_level:<15} {record.name:<20} {record.getMessage()}"
        )
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            base_format += f" [correlation_id={correlation_id}]"
        operation = getattr(record, "operation", None)
        if operation:
            base_format += f" [operation={operation}]"
        duration = getattr(record, "duration", None)
        if duration is not None:
            base_format += f" [duration={(duration * 1000):.2f}ms]"
        if record.levelno == logging.DEBUG:
            base_format += f" ({record.module}:{record.funcName}:{record.lineno})"
        if record.exc_info:
            base_format += "\n" + "".join(traceback.format_exception(*record.exc_info))
        return base_format


class ContextFilter(logging.Filter):
    "ContextFilter class for specialized functionality."

    def filter(self, record: logging.LogRecord) -> bool:
        "Filter operation."
        if not hasattr(record, "correlation_id"):
            record.correlation_id = getattr(self, "_correlation_id", None)
        if not hasattr(record, "user_id"):
            record.user_id = getattr(self, "_user_id", None)
        if not hasattr(record, "operation"):
            record.operation = getattr(self, "_operation", None)
        return True

    def set_correlation_id(self, correlation_id: str):
        "Set Correlation Id operation."
        self._correlation_id = correlation_id

    def set_user_id(self, user_id: str):
        "Set User Id operation."
        self._user_id = user_id

    def set_operation(self, operation: str):
        "Set Operation operation."
        self._operation = operation


class PerformanceLogger:
    "PerformanceLogger class for specialized functionality."

    def __init__(self, logger: logging.Logger):
        "Initialize class instance."
        self.logger = logger

    def log_operation(
        self, operation: str, duration: float, success: bool = True, **kwargs
    ):
        "Log Operation operation."
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
        "Time Operation operation."
        return OperationTimer(self, operation, **context)


class OperationTimer:
    "OperationTimer class for specialized functionality."

    def __init__(self, perf_logger: PerformanceLogger, operation: str, **context):
        "Initialize class instance."
        self.perf_logger = perf_logger
        self.operation = operation
        self.context = context
        self.start_time = None
        self.success = True

    def __enter__(self):
        "Enter   operation."
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        "Exit   operation."
        duration = time.time() - self.start_time
        self.success = exc_type is None
        self.perf_logger.log_operation(
            self.operation, duration, self.success, **self.context
        )
        return False


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: Optional[str] = None,
    max_bytes: int = ((100 * 1024) * 1024),
    backup_count: int = 5,
) -> logging.Logger:
    "Setup Logging operation."
    log_level = log_level or getattr(settings, "log_level", "INFO")
    log_format = log_format or (
        "structured" if (not getattr(settings, "debug", False)) else "development"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers.clear()
    if log_format == "structured":
        formatter = StructuredFormatter()
    else:
        formatter = DevelopmentFormatter()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    context_filter = ContextFilter()
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter())
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    "Get logger data."
    return logging.getLogger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    "Get performance logger data."
    logger = get_logger(name)
    return PerformanceLogger(logger)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    "Set Correlation Id operation."
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_correlation_id(correlation_id)
    return correlation_id


def set_user_context(user_id: str):
    "Set User Context operation."
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_user_id(user_id)


def set_operation_context(operation: str):
    "Set Operation Context operation."
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ContextFilter):
                filter_obj.set_operation(operation)


_logger = setup_logging()
