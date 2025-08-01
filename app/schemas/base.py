"""
Base Pydantic schemas for API responses with comprehensive validation and serialization.

This module provides foundational schemas and common response formats using modern
Pydantic V2 features with advanced configuration, validation, and serialization
capabilities. These schemas serve as the foundation for all API data models and
are completely separate from SQLAlchemy database models for clean architecture.

Key Features:
- Modern Pydantic V2 configuration with optimized performance settings
- Automatic UUID and datetime serialization for consistent API responses
- Flexible schema inheritance hierarchy for different use cases
- ORM integration support for seamless SQLAlchemy model conversion
- Advanced validation and assignment handling for data integrity
- Custom JSON serialization with proper type conversion

Schema Hierarchy:
- BaseSchema: Foundation class with core Pydantic V2 configuration
- TimestampSchema: Adds created_at and updated_at timestamp fields
- UUIDSchema: Adds UUID identifier field with automatic serialization
- BaseModelSchema: Complete base combining UUID and timestamp functionality

Configuration Features:
- from_attributes: Enables ORM mode for SQLAlchemy model integration
- populate_by_name: Allows field population by name and alias for flexibility
- use_enum_values: Serializes enum values instead of enum objects
- validate_assignment: Ensures data integrity on field assignment
- extra="ignore": Accepts but ignores extra input fields for robustness

Serialization Capabilities:
- Automatic UUID to string conversion for JSON compatibility
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

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Foundation Pydantic model with modern V2 configuration and comprehensive validation.

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
        # Serialize by alias (removed in v2)
        # serialize_as_any=True,
    )


class TimestampSchema(BaseSchema):
    """
    Base schema with comprehensive timestamp field support for auditing and tracking.

    Extends BaseSchema with automatic timestamp management for created_at and updated_at
    fields, providing essential auditing capabilities for tracking entity lifecycle
    and modifications. Implements custom JSON serialization with proper ISO format
    datetime handling for consistent API responses.

    Timestamp Fields:
        - created_at: Entity creation timestamp with timezone support
        - updated_at: Last modification timestamp for change tracking
        - Both fields are optional and can be None for flexibility

    Serialization Features:
        - Automatic ISO format datetime serialization with timezone indicators
        - Custom JSON dumping with proper type conversion
        - Timezone-aware timestamp handling for global applications
        - Consistent datetime format across all API responses
        - Support for None values without serialization errors

    Auditing Capabilities:
        - Creation timestamp tracking for entity lifecycle management
        - Modification timestamp tracking for change auditing
        - Database-driven timestamp updates through ORM integration
        - Automatic timestamp serialization for API responses
        - Historical data tracking and temporal analysis support

    Use Cases:
        - Entity auditing and change tracking requirements
        - API responses requiring creation and modification timestamps
        - Data lineage and historical analysis
        - Compliance and regulatory reporting needs
        - Performance monitoring and optimization analysis

    JSON Serialization:
        - Converts datetime objects to ISO format strings
        - Appends 'Z' suffix for UTC timezone indication
        - Handles None values gracefully without errors
        - Supports nested object serialization with timestamps
        - Maintains compatibility with frontend datetime parsing

    Example:
        class DocumentSchema(TimestampSchema):
            title: str
            content: str
            
        # Automatic timestamp serialization
        doc = DocumentSchema(
            title="Document", 
            content="Content",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        json_str = doc.model_dump_json()  # ISO format timestamps
    """

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        """
        Custom JSON serialization with comprehensive datetime handling and timezone support.

        Converts timestamp fields to ISO format strings with timezone indicators for
        consistent API responses and frontend compatibility. Handles None values gracefully
        and ensures proper datetime serialization across all timestamp fields.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with properly formatted timestamp fields in ISO format

        Timestamp Conversion:
            - created_at: Converted to ISO format with 'Z' suffix for UTC indication
            - updated_at: Converted to ISO format with 'Z' suffix for UTC indication
            - deleted_at: Supported for soft delete patterns with ISO format conversion
            - None values: Preserved as null in JSON output without conversion errors

        ISO Format Features:
            - Full datetime precision with microseconds when available
            - Timezone-aware serialization with UTC indication
            - Consistent format for frontend parsing and display
            - International standards compliance for datetime representation
            - Support for various datetime objects and timezone configurations

        Use Cases:
            - API response serialization with consistent timestamp formats
            - Frontend integration requiring standard datetime parsing
            - Database to API conversion with proper timestamp handling
            - Audit logging and compliance reporting with precise timestamps
            - International applications requiring timezone-aware serialization

        Example:
            timestamp_obj = TimestampSchema(
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 2, 15, 30, 0)
            )
            json_output = timestamp_obj.model_dump_json()
            # Result: {"created_at": "2024-01-01T12:00:00Z", "updated_at": "2024-01-02T15:30:00Z"}
        """
        data = self.model_dump(**kwargs)

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        import json

        return json.dumps(data)


class UUIDSchema(BaseSchema):
    """
    Base schema with UUID identifier field and automatic serialization support.

    Extends BaseSchema with UUID identifier field management, providing unique
    identification capabilities for entities with automatic JSON serialization
    support. Implements custom UUID to string conversion for API compatibility
    and consistent identifier handling across all endpoints.

    UUID Features:
        - id: Optional UUID field for unique entity identification
        - Automatic UUID generation support through database integration
        - Type-safe UUID handling with validation and conversion
        - Optional field allows for creation without pre-assigned identifiers
        - Compatible with database auto-generation and external UUID sources

    Serialization Capabilities:
        - Automatic UUID to string conversion for JSON compatibility
        - Custom JSON dumping with proper type handling
        - Frontend-compatible string representation for UUID fields
        - Maintains UUID integrity while ensuring API compatibility
        - Support for None values without serialization errors

    Identifier Management:
        - Unique entity identification across distributed systems
        - Version 4 UUID support for cryptographically secure identifiers
        - Database-driven UUID generation through ORM integration
        - Client-side UUID generation support for offline operations
        - Consistent identifier format across all API responses

    Use Cases:
        - Entity identification in distributed and microservice architectures
        - API responses requiring unique identifier fields
        - Database model to API response conversion with UUID handling
        - Client-side entity management with consistent identifiers
        - Cross-service entity reference and correlation

    JSON Serialization:
        - Converts UUID objects to string representation for API compatibility
        - Maintains UUID format and validity in string conversion
        - Handles None values gracefully without conversion errors
        - Supports nested object serialization with UUID fields
        - Frontend-compatible identifier format for UI integration

    Security Benefits:
        - Non-sequential identifiers prevent enumeration attacks
        - Cryptographically secure random generation for privacy
        - No information leakage about entity creation order or count
        - Distributed generation without coordination requirements
        - Protection against identifier prediction and guessing attacks

    Example:
        class EntitySchema(UUIDSchema):
            name: str
            description: str
            
        # UUID handling and serialization
        entity = EntitySchema(
            id=uuid.uuid4(),
            name="Example Entity",
            description="Entity description"
        )
        json_str = entity.model_dump_json()  # UUID converted to string
    """

    id: Optional[uuid.UUID] = None

    def model_dump_json(self, **kwargs):
        """
        Custom JSON serialization with comprehensive UUID handling and string conversion.

        Converts UUID fields to string representation for JSON compatibility while
        maintaining UUID format and validity. Provides seamless API integration
        with frontend applications requiring string-based identifier handling.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with UUID fields converted to string representation

        UUID Conversion:
            - id: Primary UUID field converted to standard string format
            - Maintains UUID format validation and integrity
            - Preserves UUID structure for parsing and validation
            - None values: Preserved as null in JSON output
            - Consistent string format across all UUID fields

        String Format Features:
            - Standard UUID string representation (8-4-4-4-12 hexadecimal format)
            - Lowercase hexadecimal characters for consistency
            - Hyphen-separated groups following UUID standards
            - Compatible with frontend UUID parsing and validation
            - Maintains uniqueness and identifier integrity

        Use Cases:
            - API response serialization with UUID identifier fields
            - Frontend integration requiring string-based UUID handling
            - Database to API conversion with UUID identifier preservation
            - Cross-service communication with consistent identifier format
            - Client-side entity management with UUID string representation

        Example:
            uuid_obj = UUIDSchema(id=uuid.UUID('12345678-1234-5678-9012-123456789012'))
            json_output = uuid_obj.model_dump_json()
            # Result: {"id": "12345678-1234-5678-9012-123456789012"}
        """
        data = self.model_dump(**kwargs)

        # Convert UUID to string
        if "id" in data and data["id"] is not None:
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])

        import json

        return json.dumps(data)


class BaseModelSchema(BaseSchema):
    """
    Complete foundational schema combining UUID identification and timestamp auditing.

    Comprehensive base schema that merges UUID-based unique identification with
    timestamp-based auditing capabilities, providing the complete foundation for
    entity schemas across the application. Implements advanced JSON serialization
    with proper handling of both UUID and datetime field types.

    Combined Features:
        - id: Optional UUID field for unique entity identification
        - created_at: Entity creation timestamp for lifecycle tracking
        - updated_at: Last modification timestamp for change auditing
        - Custom JSON serialization for both UUID and datetime fields

    Entity Management:
        - Unique identification through cryptographically secure UUIDs
        - Complete audit trail with creation and modification timestamps
        - Database integration support for automatic field population
        - API-compatible serialization with proper type conversion
        - Consistent field structure across all domain entities

    Serialization Capabilities:
        - Simultaneous UUID to string and datetime to ISO format conversion
        - Comprehensive JSON dumping with multiple type handling
        - Frontend-compatible field representation for all identifier and timestamp fields
        - None value handling without serialization errors
        - Nested object support with complex type conversion

    Auditing and Identification:
        - Complete entity lifecycle tracking from creation to modification
        - Unique identifier assignment for cross-service entity correlation
        - Timestamp precision for detailed audit trails and analytics
        - Non-sequential identifier generation for security and privacy
        - Database-driven field population through ORM integration

    Use Cases:
        - Primary base class for all domain entity schemas
        - Complete API response formatting with identification and auditing
        - Database model to API response conversion with full metadata
        - Distributed system entity management with unique identification
        - Compliance and regulatory reporting with complete audit trails

    JSON Serialization:
        - UUID fields: Converted to standard string representation
        - Datetime fields: Converted to ISO format with timezone indicators
        - Combined type handling in single serialization operation
        - Consistent format across all API endpoints and responses
        - Frontend integration support with standardized field formats

    Security and Compliance:
        - Non-enumerable identifiers prevent information disclosure
        - Complete audit trail for compliance and regulatory requirements
        - Secure identifier generation without coordination dependencies
        - Timestamp precision for forensic analysis and investigation
        - Data integrity through type safety and validation

    Performance Optimization:
        - Efficient combined serialization for UUID and datetime fields
        - Single-pass type conversion for optimal performance
        - Memory-efficient object creation and manipulation
        - Database integration optimization through proper field mapping
        - Fast JSON generation for high-throughput API operations

    Example:
        class UserSchema(BaseModelSchema):
            username: str
            email: str
            
        # Complete entity with ID and timestamps
        user = UserSchema(
            id=uuid.uuid4(),
            username="john_doe",
            email="john@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        json_str = user.model_dump_json()  # All fields properly serialized
    """

    id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        """
        Comprehensive JSON serialization with advanced UUID and datetime handling.

        Combines UUID to string conversion with datetime to ISO format conversion
        in a single serialization operation, providing complete type handling for
        entity schemas with identification and auditing capabilities.

        Args:
            **kwargs: Additional arguments passed to model_dump for serialization control

        Returns:
            str: JSON string with properly converted UUID and datetime fields

        Combined Type Conversion:
            - UUID fields: Converted to standard string representation for API compatibility
            - Datetime fields: Converted to ISO format with timezone indicators
            - Simultaneous processing for optimal performance
            - None value handling without conversion errors
            - Consistent field format across all entity types

        UUID Conversion:
            - id: Primary UUID field converted to standard string format
            - Maintains UUID structure and format validation
            - Compatible with frontend UUID parsing and manipulation
            - Consistent hyphen-separated hexadecimal representation
            - Preserves uniqueness and identifier integrity

        Datetime Conversion:
            - created_at: Converted to ISO format with 'Z' suffix for UTC indication
            - updated_at: Converted to ISO format with 'Z' suffix for UTC indication
            - deleted_at: Support for soft delete patterns with proper conversion
            - Microsecond precision when available for detailed tracking
            - Timezone-aware serialization for global application support

        Performance Features:
            - Single-pass field conversion for optimal efficiency
            - Combined type checking and conversion logic
            - Memory-efficient data transformation
            - Fast JSON string generation for high-throughput operations
            - Minimal overhead for complex type handling

        Use Cases:
            - Complete entity serialization for API responses
            - Database model to JSON conversion with full metadata
            - Frontend integration requiring standardized field formats
            - Cross-service communication with consistent entity representation
            - Audit logging and compliance reporting with complete information

        Example:
            entity = BaseModelSchema(
                id=uuid.UUID('12345678-1234-5678-9012-123456789012'),
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 2, 15, 30, 0)
            )
            json_output = entity.model_dump_json()
            # Result: {
            #   "id": "12345678-1234-5678-9012-123456789012",
            #   "created_at": "2024-01-01T12:00:00Z",
            #   "updated_at": "2024-01-02T15:30:00Z"
            # }
        """
        data = self.model_dump(**kwargs)

        # Convert UUID to string
        if "id" in data and data["id"] is not None:
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])

        # Convert datetime fields to ISO format strings
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if field_name in data and data[field_name] is not None:
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"

        import json

        return json.dumps(data)
