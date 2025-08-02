"""
Comprehensive middleware framework for the AI Chatbot Platform.

This package provides enterprise-grade middleware components that handle cross-cutting
concerns across the entire application stack. The middleware framework implements
industry-standard patterns for request/response processing, security enforcement,
performance monitoring, and operational observability with comprehensive logging
and metrics collection capabilities.

Key Features:
- Request timing and performance monitoring with detailed metrics collection
- Comprehensive input validation and sanitization to prevent security vulnerabilities
- Advanced rate limiting and throttling with configurable policies and user quotas
- Structured request/response logging with security event tracking and audit trails
- Debug content inspection with configurable verbosity levels for development
- Performance profiling and optimization with real-time monitoring capabilities

Security Features:
- Input validation middleware protecting against injection attacks and malformed data
- Rate limiting middleware preventing abuse, DoS attacks, and ensuring fair usage
- Security event logging with comprehensive audit trails for compliance monitoring
- Request sanitization and validation to prevent common web application vulnerabilities
- Protection against timing attacks and security reconnaissance attempts
- Comprehensive error handling without sensitive information disclosure

Performance Features:
- High-precision request timing with microsecond accuracy for performance analysis
- Real-time performance metrics collection with statistical analysis capabilities
- Request/response size monitoring and optimization recommendations
- Database query performance tracking and slow query identification
- Memory usage monitoring and leak detection capabilities
- Automatic performance baseline establishment and anomaly detection

Monitoring and Observability:
- Structured logging with JSON format for integration with monitoring systems
- Request tracing and correlation ID support for distributed system monitoring
- Performance metrics export for integration with time-series databases
- Health check endpoints with detailed system status reporting
- Error rate monitoring and alerting integration capabilities
- User behavior analytics and usage pattern identification

Middleware Stack Order:
The middleware components are applied in a specific order to ensure proper
functionality and security. The order is carefully designed to:
1. First apply security validations (rate limiting, input validation)
2. Then apply monitoring and logging for observability
3. Finally apply performance monitoring and optimization
4. Ensure proper error handling and response formatting throughout

Integration Patterns:
- FastAPI middleware integration with proper dependency injection
- Async/await support for high-performance non-blocking operations
- Configuration-driven middleware selection and parameter tuning
- Hot-reloading support for development and testing environments
- Production-ready deployment with minimal performance overhead
- Integration with external monitoring and alerting systems

Use Cases:
- Production API security enforcement with comprehensive protection mechanisms
- Development debugging and request inspection with detailed logging capabilities
- Performance monitoring and optimization for high-traffic applications
- Security audit compliance with comprehensive event tracking and reporting
- Rate limiting for API monetization and fair usage policy enforcement
- Integration with external security and monitoring infrastructure

Deployment Considerations:
- Middleware stack is optimized for production performance with minimal latency
- Configuration supports environment-specific settings and feature toggles
- Memory efficient implementation suitable for high-concurrency environments
- Integration with container orchestration platforms and cloud infrastructure
- Support for horizontal scaling and load balancing architectures
- Comprehensive error handling and graceful degradation capabilities
"""

from .core import rate_limiting_middleware, timing_middleware, validation_middleware
from .logging import debug_content_middleware, logging_middleware

__all__ = [
    "logging_middleware",
    "debug_content_middleware",
    "timing_middleware",
    "validation_middleware",
    "rate_limiting_middleware",
]
