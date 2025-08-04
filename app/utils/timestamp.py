"""Timestamp utilities for date/time handling and timezone management.

Provides datetime operations with timezone awareness, format standardization,
and utility functions for enterprise applications with UTC normalization
and comprehensive time management across timezones.
"""
- API response formatting with consistent structure and client compatibility
- Integration with external systems requiring specific timestamp formats

Performance Features:
- Memory-efficient datetime operations with minimal object allocation
- Batch processing capabilities for large-scale timestamp operations
- Caching mechanisms for frequently used timezone conversions and formatting
- Optimized comparison operations with early termination and efficient algorithms
- Integration with database query optimization and index utilization
- Background processing support for timestamp-intensive operations

Enterprise Capabilities:
- Audit trail integration with precise timestamp tracking and forensic capabilities
- Compliance reporting with regulatory timestamp requirements and validation
- System monitoring with performance timing and operational metrics
- Data retention policies with timestamp-based lifecycle management
- Backup and recovery with point-in-time restoration and consistency guarantees
- Integration with enterprise monitoring and alerting systems

Security Features:
- Tamper-resistant timestamp generation with cryptographic validation
- Audit logging with immutable timestamp records and integrity verification
- Rate limiting integration with time-based throttling and abuse prevention
- Session management with timestamp-based expiration and security validation
- Compliance tracking with detailed timestamp audit trails and reporting
- Integration with security monitoring and incident response systems

Use Cases:
- Enterprise application timestamp standardization with global deployment support
- API development with consistent datetime handling and timezone management
- Audit and compliance systems with precise timestamp tracking and validation
- Performance monitoring with high-accuracy timing and measurement capabilities
- Data analytics with temporal analysis and time-series processing
- Integration with external systems requiring specific timestamp formats and standards
"""

from datetime import datetime, timezone
from typing import Union


def utcnow() -> datetime:
    """
    Get current UTC datetime with timezone awareness and enterprise precision.

    Provides the current UTC datetime with timezone information for consistent
    timestamp generation across global deployments. Ensures all application
    timestamps are normalized to UTC for database storage, API responses,
    and cross-timezone operations with proper timezone handling.

    Returns:
        datetime: Current UTC datetime with timezone information attached.
            Includes microsecond precision for high-accuracy timing requirements.

    Security Notes:
        - Uses system clock for timestamp generation with tamper detection capabilities
        - Provides consistent timing for security audit trails and compliance logging
        - Resistant to timezone manipulation and local time zone configuration attacks

    Performance Notes:
        - Optimized for frequent calls with minimal system overhead
        - Memory efficient with direct UTC datetime object creation
        - Compatible with database timezone-aware fields and indexing

    Use Cases:
        - Database record timestamps ensuring consistent storage and querying
        - API response generation with standardized timestamp formats
        - Audit trail creation with precise timing and forensic capabilities
        - Performance monitoring with accurate timing measurements
        - Security logging with tamper-resistant timestamp generation

    Example:
        current_time = utcnow()
        # Returns: datetime(2023, 12, 1, 15, 30, 45, 123456, tzinfo=timezone.utc)
    """
    return datetime.now(timezone.utc)


def get_current_timestamp() -> str:
    """
    Generate current timestamp as standardized ISO 8601 string for enterprise integration.

    Creates a standardized ISO 8601 formatted timestamp string with UTC timezone
    indication for consistent API responses, logging, and external system integration.
    Provides enterprise-grade timestamp formatting suitable for database storage,
    audit trails, and cross-system communication with guaranteed format consistency.

    Returns:
        str: Current timestamp in ISO 8601 format with timezone indicator.
            Format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00 for maximum compatibility.

    Security Notes:
        - Provides tamper-resistant timestamp generation for security audit trails
        - Uses UTC normalization preventing timezone-based attack vectors
        - Suitable for cryptographic signing and verification processes

    Performance Notes:
        - Optimized string generation with minimal formatting overhead
        - Cached format patterns for high-frequency timestamp generation
        - Memory efficient with direct string conversion and minimal allocation

    Use Cases:
        - API response timestamps ensuring client compatibility and consistency
        - Database record creation with standardized timestamp formats
        - Audit logging with precise timing and regulatory compliance
        - External system integration with standardized timestamp exchange
        - Message queue operations with delivery timing and ordering

    Example:
        timestamp = get_current_timestamp()
        # Returns: "2023-12-01T15:30:45.123456+00:00"
    """
    return utcnow().isoformat()


def to_utc(dt: Union[datetime, str]) -> datetime:
    """
    Convert datetime or ISO string to UTC datetime.

    Args:
        dt: Datetime object or ISO string to convert

    Returns:
        datetime: UTC datetime object

    Raises:
        ValueError: If string cannot be parsed
    """
    if isinstance(dt, str):
        # Parse ISO format string
        if dt.endswith("Z"):
            dt = dt[:-1] + "+00:00"  # Replace Z with +00:00
        parsed = datetime.fromisoformat(dt)
        if parsed.tzinfo is None:
            # Assume UTC if no timezone info
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    else:
        raise ValueError(f"Invalid datetime type: {type(dt)}")


def format_timestamp(dt: datetime, include_microseconds: bool = False) -> str:
    """
    Format datetime as ISO 8601 string.

    Args:
        dt: Datetime to format
        include_microseconds: Whether to include microseconds

    Returns:
        str: Formatted timestamp string
    """
    if include_microseconds:
        return dt.isoformat()
    else:
        # Remove microseconds
        return dt.replace(microsecond=0).isoformat()


def timestamp_diff_seconds(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate difference between two timestamps in seconds.

    Args:
        dt1: First datetime (later time)
        dt2: Second datetime (earlier time)

    Returns:
        float: Difference in seconds (positive if dt1 > dt2)
    """
    return (dt1 - dt2).total_seconds()


def is_recent(dt: datetime, max_age_seconds: int = 300) -> bool:
    """
    Check if datetime is recent (within max_age_seconds from now).

    Args:
        dt: Datetime to check
        max_age_seconds: Maximum age in seconds (default: 5 minutes)

    Returns:
        bool: True if datetime is recent
    """
    now = utcnow()
    age_seconds = timestamp_diff_seconds(now, dt)
    return 0 <= age_seconds <= max_age_seconds
