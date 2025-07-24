"Service layer for base business logic."

from abc import ABC
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.logging import StructuredLogger


class BaseService(ABC):
    "Base service for business logic operations."

    def __init__(self, db: AsyncSession, logger_name: Optional[str] = None):
        "Initialize class instance."
        self.db = db
        self._logger_name = logger_name or self.__class__.__name__.lower()
        self.logger = StructuredLogger(self._logger_name)

    def _log_operation_start(self, operation: str, **kwargs):
        "Log Operation Start operation."
        self.logger.info(f"Starting {operation}", operation=operation, **kwargs)

    def _log_operation_success(self, operation: str, **kwargs):
        "Log Operation Success operation."
        self.logger.info(
            f"Completed {operation}", operation=operation, status="success", **kwargs
        )

    def _log_operation_error(self, operation: str, error: Exception, **kwargs):
        "Log Operation Error operation."
        self.logger.error(
            f"Failed {operation}: {str(error)}",
            operation=operation,
            status="error",
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs,
        )

    async def _ensure_db_session(self):
        "Ensure Db Session operation."
        if self.db is None:
            raise RuntimeError("Database session not available")

    def _validate_input(self, input_data: dict, required_fields: list = None) -> dict:
        "Validate Input operation."
        if required_fields:
            missing_fields = [
                field for field in required_fields if (field not in input_data)
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
        return input_data

    def get_service_info(self) -> dict:
        "Get service info data."
        return {
            "service_name": self.__class__.__name__,
            "logger_name": self._logger_name,
            "has_db_session": (self.db is not None),
            "service_type": "base_service",
        }
