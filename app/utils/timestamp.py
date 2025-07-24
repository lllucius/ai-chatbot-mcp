"Utility functions for timestamp operations."

from datetime import datetime, timezone
from typing import Union


def utcnow() -> datetime:
    "Utcnow operation."
    return datetime.now(timezone.utc)


def get_current_timestamp() -> str:
    "Get current timestamp data."
    return utcnow().isoformat()


def to_utc(dt: Union[(datetime, str)]) -> datetime:
    "To Utc operation."
    if isinstance(dt, str):
        if dt.endswith("Z"):
            dt = dt[:(-1)] + "+00:00"
        parsed = datetime.fromisoformat(dt)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    else:
        raise ValueError(f"Invalid datetime type: {type(dt)}")


def format_timestamp(dt: datetime, include_microseconds: bool = False) -> str:
    "Format Timestamp operation."
    if include_microseconds:
        return dt.isoformat()
    else:
        return dt.replace(microsecond=0).isoformat()


def timestamp_diff_seconds(dt1: datetime, dt2: datetime) -> float:
    "Timestamp Diff Seconds operation."
    return (dt1 - dt2).total_seconds()


def is_recent(dt: datetime, max_age_seconds: int = 300) -> bool:
    "Check if recent condition is met."
    now = utcnow()
    age_seconds = timestamp_diff_seconds(now, dt)
    return 0 <= age_seconds <= max_age_seconds
