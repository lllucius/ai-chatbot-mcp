"""
Base service class with common functionality for all service classes.

This module provides the BaseService class that other services can inherit from
to eliminate code duplication and ensure consistent patterns across services.

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundError
from ..core.logging import StructuredLogger

ModelType = TypeVar("ModelType")


class BaseService(ABC):
    """
    Base service class with common functionality.

    This class provides common patterns used across all service classes,
    including database session management, structured logging, and common
    CRUD operations that can be reused across different services.

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

    def _validate_input(
        self, input_data: dict, required_fields: Optional[List[str]] = None
    ) -> dict:
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

    async def _get_by_id(
        self,
        model: Type[ModelType],
        entity_id: UUID,
        error_message: Optional[str] = None,
    ) -> ModelType:
        """
        Get an entity by ID with standardized error handling.

        Args:
            model: SQLAlchemy model class
            entity_id: Entity ID to fetch
            error_message: Custom error message if entity not found

        Returns:
            Model instance

        Raises:
            NotFoundError: If entity not found
        """
        result = await self.db.execute(select(model).where(model.id == entity_id))
        entity = result.scalar_one_or_none()

        if not entity:
            message = (
                error_message or f"{model.__name__} not found with ID: {entity_id}"
            )
            raise NotFoundError(message)

        return entity

    async def _get_by_field(
        self,
        model: Type[ModelType],
        field_name: str,
        field_value: Any,
        error_message: Optional[str] = None,
    ) -> ModelType:
        """
        Get an entity by a specific field with standardized error handling.

        Args:
            model: SQLAlchemy model class
            field_name: Name of the field to search by
            field_value: Value to search for
            error_message: Custom error message if entity not found

        Returns:
            Model instance

        Raises:
            NotFoundError: If entity not found
        """
        field = getattr(model, field_name)
        result = await self.db.execute(select(model).where(field == field_value))
        entity = result.scalar_one_or_none()

        if not entity:
            message = (
                error_message
                or f"{model.__name__} not found with {field_name}: {field_value}"
            )
            raise NotFoundError(message)

        return entity

    async def _list_with_filters(
        self,
        model: Type[ModelType],
        filters: Optional[List[Any]] = None,
        page: int = 1,
        size: int = 20,
        order_by: Any = None,
    ) -> tuple[List[ModelType], int]:
        """
        List entities with filters and pagination.

        Args:
            model: SQLAlchemy model class
            filters: List of filter conditions
            page: Page number (1-based)
            size: Items per page
            order_by: Order by clause

        Returns:
            Tuple of (entities list, total count)
        """
        # Build base query
        query = select(model)
        count_query = select(func.count(model.id))

        # Apply filters
        if filters:
            filter_condition = and_(*filters)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering
        if order_by is not None:
            query = query.order_by(order_by)

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        # Execute query
        result = await self.db.execute(query)
        entities = result.scalars().all()

        return list(entities), total

    async def _search_entities(
        self,
        model: Type[ModelType],
        search_fields: List[str],
        search_term: str,
        additional_filters: Optional[List[Any]] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[ModelType], int]:
        """
        Search entities across multiple fields.

        Args:
            model: SQLAlchemy model class
            search_fields: List of field names to search in
            search_term: Term to search for
            additional_filters: Additional filter conditions
            page: Page number (1-based)
            size: Items per page

        Returns:
            Tuple of (entities list, total count)
        """
        search_conditions = []
        search_pattern = f"%{search_term}%"

        # Build search conditions
        for field_name in search_fields:
            field = getattr(model, field_name)
            search_conditions.append(field.ilike(search_pattern))

        # Combine with OR for search conditions
        search_filter = or_(*search_conditions)

        # Combine with additional filters using AND
        filters = [search_filter]
        if additional_filters:
            filters.extend(additional_filters)

        return await self._list_with_filters(
            model=model, filters=filters, page=page, size=size
        )

    async def _update_entity(
        self, entity: ModelType, update_data: Dict[str, Any], exclude_none: bool = True
    ) -> ModelType:
        """
        Update an entity with provided data.

        Args:
            entity: Entity to update
            update_data: Dictionary of fields to update
            exclude_none: Whether to exclude None values from updates

        Returns:
            Updated entity
        """
        for field, value in update_data.items():
            if exclude_none and value is None:
                continue
            if hasattr(entity, field):
                setattr(entity, field, value)

        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def _delete_entity(self, entity: ModelType) -> bool:
        """
        Delete an entity.

        Args:
            entity: Entity to delete

        Returns:
            True if deleted successfully
        """
        await self.db.delete(entity)
        await self.db.commit()
        return True

    async def _bulk_update(
        self, model: Type[ModelType], filters: List[Any], update_data: Dict[str, Any]
    ) -> int:
        """
        Perform bulk update on entities matching filters.

        Args:
            model: SQLAlchemy model class
            filters: Filter conditions
            update_data: Data to update

        Returns:
            Number of updated records
        """
        query = update(model).values(**update_data)
        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

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

    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the name of this service.

        Returns:
            str: The service name
        """
        pass
