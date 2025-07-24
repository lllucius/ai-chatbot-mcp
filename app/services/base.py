"""
Base service class with common functionality for all service classes.

This module provides the BaseService class that other services can inherit from
to eliminate code duplication and ensure consistent patterns across services.

"""

from abc import ABC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.logging import StructuredLogger


class BaseService(ABC):
    """
    Base service class with common functionality.

    This class provides common patterns used across all service classes,
    including database session management and structured logging.

    Attributes:
        db: Database session for service operations
        logger: Structured logger instance for the service
        _logger_name: Name used for logger identification
    """

    def __init__(self, db: AsyncSession, logger_name: Optional[str] = None):
        """
        Initialize base service.

        Args:
            db: Database session for service operations
            logger_name: Optional custom logger name, defaults to class name
        """
        self.db = db
        self._logger_name = logger_name or self.__class__.__name__.lower()
        self.logger = StructuredLogger(self._logger_name)

    def _log_operation_start(self, operation: str, **kwargs):
        """
        Log the start of a service operation.

        Args:
            operation: Name of the operation being started
            **kwargs: Additional context data for logging
        """
        self.logger.info(f"Starting {operation}", operation=operation, **kwargs)

    def _log_operation_success(self, operation: str, **kwargs):
        """
        Log successful completion of a service operation.

        Args:
            operation: Name of the operation that completed
            **kwargs: Additional context data for logging
        """
        self.logger.info(
            f"Completed {operation}", operation=operation, status="success", **kwargs
        )

    def _log_operation_error(self, operation: str, error: Exception, **kwargs):
        """
        Log error during service operation.

        Args:
            operation: Name of the operation that failed
            error: Exception that occurred
            **kwargs: Additional context data for logging
        """
        self.logger.error(
            f"Failed {operation}: {str(error)}",
            operation=operation,
            status="error",
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs,
        )

    async def _ensure_db_session(self):
        """
        Ensure database session is available and valid.

        This method can be extended by subclasses to add additional
        database session validation or setup logic.
        """
        if self.db is None:
            raise RuntimeError("Database session not available")

        # Additional validation can be added here by subclasses

    def _validate_input(self, input_data: dict, required_fields: list = None) -> dict:
        """
        Validate input data for service operations.

        Args:
            input_data: Data to validate
            required_fields: List of required field names

        Returns:
            dict: Validated input data

        Raises:
            ValueError: If validation fails
        """
        if required_fields:
            missing_fields = [
                field for field in required_fields if field not in input_data
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        return input_data

    def get_service_info(self) -> dict:
        """
        Get information about this service instance.

        Returns:
            dict: Service information including name and status
        """
        return {
            "service_name": self.__class__.__name__,
            "logger_name": self._logger_name,
            "has_db_session": self.db is not None,
            "service_type": "base_service",
        }
