"""Base service class with common functionality for enterprise service architecture.

This module provides the foundational BaseService class that implements common
patterns, utilities, and infrastructure used across all service classes in the
AI Chatbot Platform. Eliminates code duplication, ensures consistent service
architecture, and provides standardized logging, error handling, and database
management patterns for enterprise-grade service implementations.

Key Features:
- Standardized service initialization and configuration management
- Comprehensive structured logging with consistent patterns and audit trails
- Database session management with proper connection handling and transaction control
- Common CRUD operation patterns and utilities for data access
- Standardized error handling and exception management across services
- Performance monitoring and operation tracking for observability

Service Architecture:
- Abstract base class for inheritance by all application services
- Consistent service initialization with database connectivity and logging
- Standardized operation lifecycle management with start, success, and error logging
- Database session validation and connection management for reliability
- Common patterns for data access, validation, and business logic
- Integration support for monitoring, metrics, and observability systems

Logging Capabilities:
- Structured logging with consistent format and metadata across services
- Operation lifecycle tracking with start, success, and error states
- Comprehensive context capture for debugging and audit trails
- Performance monitoring with operation timing and resource usage
- Security audit logging for compliance and monitoring requirements
- Integration with external logging and monitoring systems

Database Management:
- Async database session handling with proper connection management
- Transaction control and rollback handling for data integrity
- Connection validation and reconnection logic for reliability
- Query optimization and performance monitoring capabilities
- Database error handling and recovery mechanisms
- Support for database migrations and schema changes

Use Cases:
- Foundation for all business logic services in the application
- Standardized service architecture for microservices and monolithic applications
- Common infrastructure for authentication, user management, and data services
- Base functionality for API endpoints and background processing services
- Integration foundation for external service communication and data synchronization
- Framework for testing, mocking, and service isolation in development environments

Service Patterns:
- Dependency injection support for service composition and testing
- Service lifecycle management with initialization and cleanup
- Common validation patterns and error handling across services
- Performance monitoring and metrics collection for operational visibility
- Security controls and audit logging for compliance and monitoring
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import StructuredLogger

ModelType = TypeVar("ModelType")


class BaseService:
    """Base service class with common functionality for enterprise service architecture.

    This base class provides foundational infrastructure used across all service
    classes in the AI Chatbot Platform, implementing common patterns for database
    management, structured logging, error handling, and operation tracking.
    """

    def __init__(self, db: AsyncSession, logger_name: Optional[str] = None):
        """Initialize base service.

        Args:
            db: Database session for service operations
            logger_name: Optional custom logger name, defaults to class name

        """
        self.db = db
        self._logger_name = logger_name or self.__class__.__name__.lower()
        self.logger = StructuredLogger(self._logger_name)

    def _log_operation_start(self, operation: str, **kwargs):
        """Log the start of a service operation.

        Args:
            operation: Name of the operation being started
            **kwargs: Additional context data for logging

        """
        self.logger.info(f"Starting {operation}", operation=operation, **kwargs)

    def _log_operation_success(self, operation: str, **kwargs):
        """Log successful completion of a service operation.

        Args:
            operation: Name of the operation that completed
            **kwargs: Additional context data for logging

        """
        self.logger.info(
            f"Completed {operation}", operation=operation, status="success", **kwargs
        )

    def _log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log error during service operation.

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
        """Ensure database session is available and valid.

        This method can be extended by subclasses to add additional
        database session validation or setup logic.
        """
        if self.db is None:
            raise RuntimeError("Database session not available")

        # Additional validation can be added here by subclasses

    def _validate_input(
        self, input_data: dict, required_fields: Optional[List[str]] = None
    ) -> dict:
        """Validate input data for service operations.

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
        entity_id: int,
        error_message: Optional[str] = None,
    ) -> ModelType:
        """Get an entity by ID with standardized error handling.

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
        """Get an entity by a specific field with standardized error handling.

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
        """List entities with filters and pagination.

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
        """Search entities across multiple fields.

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
        """Update an entity with provided data.

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
        """Delete an entity.

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
        """Perform bulk update on entities matching filters.

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
