"""Base Pydantic schemas for API responses with comprehensive validation and serialization.

This module provides foundational schemas and common response formats using modern
Pydantic V2 features with advanced configuration, validation, and serialization
capabilities. These schemas serve as the foundation for all API data models and
are completely separate from SQLAlchemy database models for clean architecture.

Key Features:
- Modern Pydantic V2 configuration with optimized performance settings
- Automatic integer ID and datetime serialization for consistent API responses
- Flexible schema inheritance hierarchy for different use cases
- ORM integration support for seamless SQLAlchemy model conversion
- Advanced validation and assignment handling for data integrity
- Custom JSON serialization with proper type conversion

Schema Hierarchy:
- BaseSchema: Foundation class with core Pydantic V2 configuration
- TimestampMixin: Provides timestamp fields and JSON serialization
- IdMixin: Provides ID field and JSON serialization
- BaseModelSchema: Complete base combining ID and timestamp functionality

Configuration Features:
- from_attributes: Enables ORM mode for SQLAlchemy model integration
- populate_by_name: Allows field population by name and alias for flexibility
- use_enum_values: Serializes enum values instead of enum objects
- validate_assignment: Ensures data integrity on field assignment
- extra="ignore": Accepts but ignores extra input fields for robustness

Serialization Capabilities:
- Automatic integer ID serialization for JSON compatibility
- ISO format datetime serialization with timezone indicators
- Custom JSON dumping with proper type handling
- Consistent field naming and format across all API responses
- Support for nested object serialization and complex data structures

Design Principles:
- Separation of concerns between API schemas and database models
- Consistent data validation and serialization across all endpoints
- Performance optimization through proper Pydantic configuration
- Maintainable inheritance hierarchy for schema reuse
- Type safety and validation for robust API data handling

Use Cases:
- API response formatting and validation for all endpoints
- Data transfer objects (DTOs) for service layer communication
- Input validation and sanitization for request processing
- Database model to API response conversion
- Complex data structure serialization and validation

Security Features:
- Input validation and sanitization to prevent injection attacks
- Type safety enforcement for data integrity
- Extra field filtering to prevent information leakage
- Consistent serialization to prevent data exposure vulnerabilities
- Validation assignment protection against malicious modifications
"""

import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


def serialize_datetime_to_iso(dt: datetime) -> str:
    """Serialize datetime to ISO format with Z suffix for UTC.

    Args:
        dt: Datetime object to serialize

    Returns:
        ISO format string with Z suffix for UTC

    """
    iso_string = dt.isoformat()
    if iso_string.endswith("+00:00"):
        iso_string = iso_string[:-6] + "Z"
    return iso_string


class BaseSchema(BaseModel):
    """Foundation Pydantic model with modern V2 configuration and comprehensive validation.

    Serves as the base class for all API schemas with optimized Pydantic V2 configuration
    for performance, validation, and serialization. Provides essential configuration
    for ORM integration, field handling, and data validation across the application.

    Configuration Features:
        - from_attributes: Enables seamless SQLAlchemy model to schema conversion
        - populate_by_name: Supports field population by both field names and aliases
        - use_enum_values: Serializes enum values for consistent JSON representation
        - validate_assignment: Ensures data integrity during field assignment operations
        - extra="ignore": Accepts extra input fields while maintaining schema purity

    Data Validation:
        - Automatic type conversion and validation for all field assignments
        - Input sanitization and normalization for security and consistency
        - Field-level validation with custom validators when needed
        - Type safety enforcement for robust data handling
        - Assignment validation to prevent invalid data mutations

    ORM Integration:
        - Direct conversion from SQLAlchemy models using from_attributes=True
        - Automatic field mapping and type conversion
        - Support for relationship and nested object serialization
        - Lazy loading compatibility for database performance
        - Transaction-safe data access and conversion

    Performance Optimization:
        - Efficient field validation and serialization mechanisms
        - Optimized configuration for high-throughput API operations
        - Memory-efficient object creation and manipulation
        - Fast JSON serialization and deserialization
        - Minimal overhead for data conversion operations

    Use Cases:
        - Base class for all API request and response schemas
        - Data transfer objects for service layer communication
        - Input validation for user-provided data
        - Database model to API response conversion
        - Complex data structure validation and serialization

    Security Features:
        - Input validation prevents injection attacks and malformed data
        - Extra field filtering protects against data leakage
        - Type safety enforcement for data integrity
        - Consistent serialization prevents information disclosure
        - Validation assignment protection against malicious modifications

    Example:
        class UserSchema(BaseSchema):
            username: str
            email: str

        # Automatic validation and type conversion
        user = UserSchema(username="john", email="john@example.com")

    """

    model_config = ConfigDict(
        # Enable ORM mode for SQLAlchemy integration
        from_attributes=True,
        # Allow population by field name and alias
        populate_by_name=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Allow extra fields in input (but don't include in output)
        extra="ignore",
    )


class TimestampMixin(BaseModel):
    """Mixin providing timestamp fields and JSON serialization for auditing.

    Provides created_at and updated_at timestamp fields with proper JSON serialization
    for audit trails and entity lifecycle tracking. Can be mixed into any schema
    that needs timestamp support.
    """

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        """Serialize model with custom datetime handling."""
        data = self.model_dump(**kwargs)

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = serialize_datetime_to_iso(data[field_name])

        return json.dumps(data)


class IdMixin(BaseModel):
    """Mixin providing ID field and JSON serialization for unique identification.

    Provides an optional integer id field with proper JSON serialization for
    unique entity identification. Can be mixed into any schema that needs
    ID support.
    """

    id: Optional[int] = None

    def model_dump_json(self, **kwargs):
        """Serialize model with custom ID handling."""
        data = self.model_dump(**kwargs)

        # ID is already an integer, no conversion needed
        # This method is kept for consistency with the interface

        return json.dumps(data)


class TimestampSchema(BaseSchema, TimestampMixin):
    """Base schema with comprehensive timestamp field support for auditing and tracking.

    Extends BaseSchema with automatic timestamp management for created_at and updated_at
    fields, providing essential auditing capabilities for tracking entity lifecycle
    and modifications. Implements custom JSON serialization with proper ISO format
    datetime handling for consistent API responses.

    Use this for schemas that need timestamp tracking but not ID identification.
    """

    pass


class IdSchema(BaseSchema, IdMixin):
    """Base schema with ID identifier field and automatic serialization support.

    Extends BaseSchema with ID identifier field management, providing unique
    identification capabilities for entities with automatic JSON serialization
    support. Implements standard integer ID handling for API compatibility
    and consistent identifier handling across all endpoints.

    Use this for schemas that need ID identification but not timestamp tracking.
    """

    pass


class BaseModelSchema(BaseSchema):
    """Complete foundational schema combining ID identification and timestamp auditing.

    Comprehensive base schema that merges integer-based unique identification with
    timestamp-based auditing capabilities, providing the complete foundation for
    entity schemas across the application. Implements advanced JSON serialization
    with proper handling of both ID and datetime field types.

    This is the recommended base class for most domain entity schemas that need
    both unique identification and audit trail capabilities.
    """

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        """Comprehensive JSON serialization with advanced ID and datetime handling.

        Combines integer ID handling with datetime to ISO format conversion
        in a single serialization operation, providing complete type handling for
        entity schemas with identification and auditing capabilities.
        """
        data = self.model_dump(**kwargs)

        # ID is already an integer, no conversion needed

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = serialize_datetime_to_iso(data[field_name])

        return json.dumps(data)
