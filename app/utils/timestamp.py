"""
Timestamp utilities for consistent date/time handling.

This module provides standardized functions for generating timestamps
and working with UTC datetime objects across the application.

"""

from datetime import datetime, timezone
from typing import Union


def utcnow() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def get_current_timestamp() -> str:
    """
    Get current timestamp as ISO 8601 string.

    Returns:
        str: Current timestamp in ISO 8601 format
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
