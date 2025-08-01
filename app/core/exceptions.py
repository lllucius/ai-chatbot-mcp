"""
Custom exception classes for the AI Chatbot Platform with comprehensive error handling.

This module defines application-specific exceptions with structured error codes,
detailed messages, and comprehensive error context for robust error handling,
debugging, and monitoring. Implements a hierarchical exception structure for
different types of errors with consistent error reporting and logging capabilities.

Key Features:
- Hierarchical exception structure with common base class
- Structured error codes for machine-readable error identification
- Comprehensive error details and context information
- Consistent error message formatting and reporting
- Integration with logging and monitoring systems
- Debug-friendly error information for development and troubleshooting

Exception Hierarchy:
- ChatbotPlatformException: Base class for all application exceptions
- ValidationError: Input validation and data integrity errors
- AuthenticationError: User authentication and credential errors
- AuthorizationError: Access control and permission errors
- NotFoundError: Resource not found and missing entity errors
- DocumentError: Document processing and manipulation errors
- EmbeddingError: Vector embedding and similarity search errors
- ExternalServiceError: Third-party service integration errors
- ConfigurationError: Application configuration and setup errors
- RateLimitError: API rate limiting and throttling errors
- SearchError: Search functionality and query processing errors

Error Handling Features:
- Structured error codes for automated error processing
- Detailed error messages for user-friendly error reporting
- Additional error context and metadata for debugging
- Consistent error format across all application components
- Integration with exception handling middleware and logging
- Support for error tracking and monitoring systems

Use Cases:
- API error responses with structured error information
- Service layer error handling and propagation
- User interface error display and feedback
- System monitoring and alerting integration
- Debugging and troubleshooting support
- Audit logging and compliance reporting

Error Reporting:
- Human-readable error messages for user interfaces
- Machine-readable error codes for automated processing
- Detailed error context for debugging and analysis
- Consistent error structure for frontend integration
- Comprehensive error logging for monitoring and analysis
- Integration with error tracking and reporting systems

Security Considerations:
- Error messages sanitized to prevent information disclosure
- Sensitive information excluded from error details
- Proper error logging without exposing credentials or secrets
- Error rate monitoring for security incident detection
- Protection against error-based information leakage
- Secure error handling in authentication and authorization flows
"""

from typing import Any, Dict, Optional


class ChatbotPlatformException(Exception):
    """
    Base exception class for all application-specific exceptions with comprehensive error handling.

    Provides the foundational structure for all custom exceptions in the AI Chatbot Platform
    with standardized error codes, detailed messages, and additional context information.
    Implements consistent error handling patterns across the application for robust error
    management, debugging, and monitoring capabilities.

    Error Structure:
        - message: Human-readable error description for user interfaces and logging
        - error_code: Machine-readable identifier for automated error processing
        - details: Additional context and metadata for debugging and analysis

    Error Handling Features:
        - Structured error information for consistent API responses
        - Machine-readable error codes for automated error processing
        - Detailed error context for debugging and troubleshooting
        - Consistent error format across all application components
        - Integration with logging and monitoring systems

    Use Cases:
        - Base class for all domain-specific exceptions
        - Structured error responses for API endpoints
        - Error logging and monitoring integration
        - Debugging and troubleshooting support
        - User interface error display and feedback

    Error Code Standards:
        - Standardized error codes for consistent error identification
        - Machine-readable format for automated error processing
        - Hierarchical error code structure for error categorization
        - Integration with error tracking and monitoring systems
        - Support for internationalization and localization

    Example:
        try:
            # Some operation that might fail
            perform_operation()
        except ChatbotPlatformException as e:
            logger.error(f"Operation failed: {e.error_code} - {e.message}", extra=e.details)
            return {"error": e.error_code, "message": e.message, "details": e.details}
    """

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize base exception with comprehensive error information and context.

        Creates a structured exception with error code, message, and additional details
        for robust error handling, logging, and monitoring. Provides consistent error
        structure across all application components for unified error management.

        Args:
            message: Human-readable error description for user interfaces and logging
            error_code: Machine-readable error identifier for automated processing
            details: Additional error context and metadata for debugging and analysis

        Error Message Guidelines:
            - Clear and descriptive error descriptions for user understanding
            - Technical details appropriate for the target audience
            - Avoid sensitive information exposure in error messages
            - Consistent message formatting and language across exceptions
            - Actionable information when possible for error resolution

        Error Code Standards:
            - Uppercase snake_case format for consistency (e.g., "VALIDATION_ERROR")
            - Descriptive codes that clearly identify the error type
            - Hierarchical structure for error categorization
            - Unique codes to prevent ambiguity in error identification
            - Integration with error tracking and monitoring systems

        Error Details:
            - Additional context information for debugging and analysis
            - Structured data for automated error processing
            - Technical details for development and troubleshooting
            - User-safe information that doesn't expose sensitive data
            - Integration with logging and monitoring metadata

        Example:
            # Basic exception with default error code
            raise ChatbotPlatformException("Operation failed")
            
            # Exception with specific error code and details
            raise ChatbotPlatformException(
                message="Database connection failed",
                error_code="DATABASE_CONNECTION_ERROR",
                details={"host": "db.example.com", "port": 5432, "retry_count": 3}
            )
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatbotPlatformException):
    """
    Exception raised when input validation fails with comprehensive validation context.

    Specialized exception for handling input validation errors including field validation,
    data integrity checks, business rule violations, and schema validation failures.
    Provides detailed validation context for user feedback and debugging support.

    Validation Scenarios:
        - Field validation failures with specific field information
        - Data type and format validation errors
        - Business rule violations and constraint failures
        - Schema validation errors for complex data structures
        - Cross-field validation and dependency errors

    Error Context:
        - Specific field names and validation rules that failed
        - Expected vs actual values for validation comparison
        - Multiple validation errors aggregated in details
        - User-friendly error messages for form validation
        - Technical validation details for debugging

    Use Cases:
        - API request validation with detailed field-level errors
        - Form submission validation in user interfaces
        - Data import validation with comprehensive error reporting
        - Business rule enforcement with clear violation descriptions
        - Schema validation for complex data structures and configurations

    Integration:
        - FastAPI request validation error handling
        - Pydantic model validation error processing
        - Custom business rule validation reporting
        - User interface validation feedback systems
        - Data quality monitoring and reporting

    Example:
        raise ValidationError(
            message="User registration validation failed",
            details={
                "username": "Username must contain only alphanumeric characters",
                "email": "Invalid email format",
                "password": "Password must contain at least one uppercase letter"
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(ChatbotPlatformException):
    """
    Exception raised when user authentication fails with comprehensive security context.

    Specialized exception for handling authentication failures including credential
    validation, token verification, multi-factor authentication, and session management
    errors. Provides security-focused error reporting without exposing sensitive information.

    Authentication Scenarios:
        - Invalid username or password credentials
        - JWT token validation and expiration errors
        - Multi-factor authentication failures
        - Session timeout and invalidation errors
        - Account lockout and security restrictions

    Security Features:
        - Error messages that don't expose sensitive authentication details
        - Rate limiting integration for brute force protection
        - Audit logging for security monitoring and analysis
        - Account lockout tracking and management
        - Comprehensive security event reporting

    Error Context:
        - Authentication method that failed (password, token, MFA)
        - Account status information (active, locked, expired)
        - Security-related metadata for monitoring
        - User-safe error messages that don't expose system details
        - Technical error information for security analysis

    Use Cases:
        - Login form authentication error handling
        - API authentication and token validation failures
        - Multi-factor authentication error reporting
        - Session management and timeout handling
        - Security monitoring and incident response

    Security Considerations:
        - Error messages avoid exposing user existence or account details
        - Failed authentication attempts logged for security monitoring
        - Rate limiting integration to prevent brute force attacks
        - Account lockout mechanisms to protect against abuse
        - Audit trails for security compliance and investigation

    Example:
        raise AuthenticationError(
            message="Authentication failed",
            details={
                "method": "password",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "attempt_count": 3
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(ChatbotPlatformException):
    """
    Exception raised when user authorization fails with comprehensive access control context.

    Specialized exception for handling authorization and access control failures including
    permission violations, role-based access control errors, resource ownership validation,
    and administrative privilege requirements. Provides detailed access control context
    for security monitoring and user feedback.

    Authorization Scenarios:
        - Insufficient permissions for requested operations
        - Role-based access control violations
        - Resource ownership and access rights validation
        - Administrative privilege requirement failures
        - Cross-tenant access control violations

    Access Control Features:
        - Detailed permission and role requirement information
        - Resource ownership validation and reporting
        - Administrative privilege checking and enforcement
        - Cross-tenant security boundary enforcement
        - Comprehensive access control audit logging

    Error Context:
        - Required permissions or roles for the operation
        - User's current permissions and role assignments
        - Resource identifier and ownership information
        - Operation attempted and access control policy applied
        - Security context for audit and compliance reporting

    Use Cases:
        - API endpoint access control enforcement
        - Administrative interface permission validation
        - Resource ownership verification for data operations
        - Multi-tenant access control and isolation
        - Security policy enforcement and compliance monitoring

    Security Monitoring:
        - Access control violations logged for security analysis
        - Permission escalation attempts tracked and reported
        - Resource access patterns monitored for anomaly detection
        - Administrative access audit trails for compliance
        - Security policy violations reported for incident response

    Example:
        raise AuthorizationError(
            message="Insufficient permissions to access user management",
            details={
                "required_permission": "users:admin",
                "user_permissions": ["users:read", "profiles:write"],
                "resource": "users",
                "operation": "admin_list"
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class NotFoundError(ChatbotPlatformException):
    """
    Exception raised when requested resources are not found with comprehensive resource context.

    Specialized exception for handling resource not found scenarios including entity lookup
    failures, missing files, unavailable services, and resource lifecycle management.
    Provides detailed resource context for debugging and user feedback.

    Resource Scenarios:
        - Database entity not found by identifier
        - File system resources missing or inaccessible
        - External service endpoints not available
        - API resources that have been deleted or archived
        - Configuration resources missing or misconfigured

    Resource Context:
        - Resource type and identifier for specific lookup information
        - Search criteria and parameters used for resource discovery
        - Related resources and dependencies for context
        - Resource lifecycle status and availability information
        - Alternative resources or suggestions for resolution

    Error Reporting:
        - Clear identification of the missing resource type
        - Specific resource identifiers for debugging
        - Search parameters that led to the not found condition
        - Suggestions for alternative resources or actions
        - Technical details for troubleshooting and resolution

    Use Cases:
        - API endpoint resource lookup failures
        - Database entity retrieval with invalid identifiers
        - File system operations on missing files
        - External service integration with unavailable resources
        - Configuration management with missing settings

    User Experience:
        - Clear error messages for missing resources
        - Helpful suggestions for alternative actions
        - Resource discovery assistance for users
        - Context-aware error reporting for better understanding
        - Integration with search and suggestion systems

    Example:
        raise NotFoundError(
            message="User not found",
            details={
                "resource_type": "user",
                "identifier": "user_123",
                "search_criteria": {"username": "john_doe"},
                "available_actions": ["search_users", "create_user"]
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NOT_FOUND_ERROR", details)


class DocumentError(ChatbotPlatformException):
    """
    Exception raised when document processing operations fail with comprehensive processing context.

    Specialized exception for handling document processing failures including file parsing,
    content extraction, format conversion, metadata processing, and storage operations.
    Provides detailed processing context for debugging and error recovery.

    Document Processing Scenarios:
        - File format parsing and content extraction failures
        - Document validation and integrity checking errors
        - Metadata extraction and processing issues
        - File storage and retrieval operation failures
        - Document conversion and transformation errors

    Processing Context:
        - Document type, format, and size information
        - Processing stage where the error occurred
        - File metadata and characteristics
        - Error details specific to document processing
        - Recovery suggestions and alternative processing options

    Error Categories:
        - File format and parsing errors with specific format details
        - Content extraction failures with processing stage information
        - Storage operation errors with file system or database context
        - Validation errors with document integrity and compliance issues
        - Conversion errors with format transformation details

    Use Cases:
        - Document upload and processing pipeline errors
        - File format validation and compatibility checking
        - Content extraction for search indexing and analysis
        - Document storage and retrieval operations
        - Metadata processing and enrichment workflows

    Recovery Assistance:
        - Alternative processing methods and formats
        - Manual processing options for complex documents
        - File format conversion suggestions
        - Document repair and validation tools
        - Technical support information for complex issues

    Example:
        raise DocumentError(
            message="Failed to extract text from PDF document",
            details={
                "document_id": "doc_123",
                "file_name": "report.pdf",
                "file_size": 2048576,
                "processing_stage": "text_extraction",
                "error_details": "Encrypted PDF requires password",
                "suggested_actions": ["provide_password", "try_ocr"]
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_ERROR", details)


class EmbeddingError(ChatbotPlatformException):
    """
    Exception raised when vector embedding operations fail with comprehensive embedding context.

    Specialized exception for handling vector embedding and similarity search failures including
    text embedding generation, vector storage operations, similarity calculations, and index
    management. Provides detailed embedding context for debugging and performance optimization.

    Embedding Scenarios:
        - Text-to-vector embedding generation failures
        - Vector database storage and retrieval errors
        - Similarity search and ranking operation failures
        - Embedding model loading and initialization errors
        - Vector index creation and maintenance issues

    Embedding Context:
        - Embedding model information and configuration
        - Text input characteristics and preprocessing details
        - Vector dimensions and mathematical operation context
        - Performance metrics and timing information
        - Alternative embedding methods and models

    Technical Details:
        - Embedding model type, version, and configuration parameters
        - Input text length, language, and preprocessing applied
        - Vector dimensions, data types, and storage format
        - Similarity metrics and distance calculation methods
        - Performance benchmarks and optimization suggestions

    Use Cases:
        - Document embedding for semantic search and retrieval
        - Conversation context embedding for AI assistant integration
        - Content similarity analysis and recommendation systems
        - Vector database operations and index management
        - Machine learning pipeline integration with embedding models

    Performance Optimization:
        - Embedding batch processing for improved throughput
        - Vector compression and storage optimization techniques
        - Similarity search algorithm tuning and optimization
        - Embedding model selection and performance comparison
        - Caching strategies for frequently accessed embeddings

    Example:
        raise EmbeddingError(
            message="Failed to generate embeddings for document content",
            details={
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "input_length": 5000,
                "vector_dimension": 384,
                "error_stage": "model_inference",
                "performance_metrics": {"processing_time": 2.5, "memory_usage": "512MB"}
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)


class ExternalServiceError(ChatbotPlatformException):
    """
    Exception raised when external service integration fails with comprehensive service context.

    Specialized exception for handling third-party service integration failures including
    API calls, service availability, authentication issues, rate limiting, and data format
    incompatibilities. Provides detailed service context for debugging and resilience planning.

    Service Integration Scenarios:
        - API endpoint connectivity and availability issues
        - Authentication and authorization failures with external services
        - Rate limiting and quota exhaustion from service providers
        - Data format and protocol compatibility problems
        - Service degradation and performance issues

    Service Context:
        - Service provider information and endpoint details
        - Request and response data for debugging
        - Authentication method and credential status
        - Rate limiting and quota usage information
        - Alternative services and fallback options

    Resilience Features:
        - Retry logic and backoff strategy recommendations
        - Circuit breaker patterns for service protection
        - Fallback service options and degraded functionality
        - Service health monitoring and status reporting
        - Performance metrics and optimization suggestions

    Use Cases:
        - OpenAI API integration for language model operations
        - FastMCP service integration for tool management
        - Third-party authentication providers (OAuth, SAML)
        - External data sources and content repositories
        - Notification and communication service integrations

    Service Monitoring:
        - Service availability and response time tracking
        - Error rate monitoring and alerting
        - Quota usage tracking and optimization
        - Service dependency mapping and impact analysis
        - Performance benchmarking and optimization recommendations

    Example:
        raise ExternalServiceError(
            message="OpenAI API request failed",
            details={
                "service": "openai",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "status_code": 429,
                "error_type": "rate_limit_exceeded",
                "retry_after": 60,
                "fallback_options": ["azure_openai", "local_llm"]
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(ChatbotPlatformException):
    """
    Exception raised when application configuration is invalid with comprehensive configuration context.

    Specialized exception for handling configuration errors including missing settings,
    invalid values, environment variable issues, and configuration file problems.
    Provides detailed configuration context for system administration and deployment.

    Configuration Scenarios:
        - Missing required configuration settings and environment variables
        - Invalid configuration values and format validation errors
        - Configuration file parsing and loading issues
        - Environment-specific configuration conflicts and inconsistencies
        - Database connection and external service configuration problems

    Configuration Context:
        - Specific configuration keys and sections affected
        - Expected vs actual configuration values
        - Configuration source (file, environment, database)
        - Validation rules and requirements
        - Configuration examples and documentation references

    System Administration:
        - Configuration validation and testing tools
        - Environment-specific configuration management
        - Configuration backup and recovery procedures
        - Configuration deployment and rollback strategies
        - Configuration security and access control

    Use Cases:
        - Application startup and initialization failures
        - Environment variable validation and setup
        - Configuration file parsing and loading errors
        - Database connection configuration issues
        - External service integration configuration problems

    Resolution Assistance:
        - Configuration examples and template references
        - Validation tools and testing procedures
        - Documentation links and setup guides
        - Environment-specific configuration recommendations
        - Troubleshooting steps and diagnostic information

    Example:
        raise ConfigurationError(
            message="Database connection configuration is invalid",
            details={
                "setting": "DATABASE_URL",
                "provided_value": "postgresql://user@invalid-host:5432/db",
                "validation_error": "Host 'invalid-host' is not resolvable",
                "expected_format": "postgresql://user:password@host:port/database",
                "documentation": "https://docs.example.com/database-setup"
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class RateLimitError(ChatbotPlatformException):
    """
    Exception raised when API rate limits are exceeded with comprehensive rate limiting context.

    Specialized exception for handling rate limiting scenarios including request throttling,
    quota exhaustion, user-specific limits, and service protection mechanisms. Provides
    detailed rate limiting context for client applications and monitoring systems.

    Rate Limiting Scenarios:
        - Per-user API request rate limit enforcement
        - Global service rate limiting and capacity protection
        - Resource-specific usage quotas and restrictions
        - Time-based rate limiting with sliding windows
        - External service rate limit propagation and handling

    Rate Limiting Context:
        - Current usage statistics and rate limit thresholds
        - Time window information and reset timestamps
        - User-specific quotas and usage patterns
        - Resource type and operation rate limiting details
        - Retry recommendations and backoff strategies

    Client Guidance:
        - Retry-After header information for optimal retry timing
        - Rate limit reset time for planning subsequent requests
        - Alternative endpoints or methods with different limits
        - Quota upgrade options and pricing information
        - Usage optimization recommendations and best practices

    Use Cases:
        - API endpoint protection and capacity management
        - User quota enforcement and billing integration
        - External service rate limit handling and propagation
        - Abuse prevention and system protection
        - Fair usage policy enforcement and monitoring

    Monitoring Integration:
        - Rate limit usage tracking and analytics
        - Abuse detection and pattern analysis
        - Capacity planning and scaling recommendations
        - Client behavior analysis and optimization
        - Service level agreement monitoring and reporting

    Example:
        raise RateLimitError(
            message="API rate limit exceeded",
            details={
                "limit_type": "requests_per_minute",
                "current_usage": 1000,
                "rate_limit": 1000,
                "reset_time": "2024-01-01T12:01:00Z",
                "retry_after": 60,
                "quota_info": {"daily_limit": 10000, "daily_usage": 8500}
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class SearchError(ChatbotPlatformException):
    """
    Exception raised when search operations fail with comprehensive search context.

    Specialized exception for handling search functionality failures including query parsing,
    index operations, ranking algorithms, and result processing. Provides detailed search
    context for debugging and search experience optimization.

    Search Operation Scenarios:
        - Search query parsing and validation failures
        - Search index corruption or unavailability issues
        - Ranking algorithm errors and scoring problems
        - Search result processing and formatting failures
        - Search performance and timeout issues

    Search Context:
        - Query text, parameters, and preprocessing details
        - Search index information and configuration
        - Ranking algorithm and scoring mechanism details
        - Performance metrics and timing information
        - Alternative search methods and fallback options

    Search Optimization:
        - Query suggestion and auto-correction recommendations
        - Index optimization and maintenance strategies
        - Ranking algorithm tuning and improvement suggestions
        - Search performance analysis and bottleneck identification
        - User experience enhancement recommendations

    Use Cases:
        - Document search and content discovery operations
        - User search queries and result processing
        - Advanced search features and filtering operations
        - Search analytics and performance monitoring
        - Search index management and maintenance

    Performance Analysis:
        - Query execution time and resource usage metrics
        - Index size and search space analysis
        - Result relevance and ranking quality assessment
        - Search traffic patterns and usage analytics
        - System capacity and scalability recommendations

    Example:
        raise SearchError(
            message="Search query processing failed",
            details={
                "query": "artificial intelligence chatbot",
                "search_type": "semantic_search",
                "index": "documents_v2",
                "error_stage": "vector_similarity",
                "performance_metrics": {"query_time": 5.2, "results_count": 0},
                "suggestions": ["try_keyword_search", "adjust_similarity_threshold"]
            }
        )
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SEARCH_ERROR", details)
