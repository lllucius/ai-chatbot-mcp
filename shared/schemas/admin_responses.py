"""
Administrative and database response schemas.

This module contains response schemas for administrative operations, database management,
and system monitoring that were previously scattered across common.py.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import serialize_datetime_to_iso


def utcnow() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


# --- Database Response Models ---


class DatabaseStatusResponse(BaseModel):
    """Database status response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    connection_status: str = Field(..., description="Database connection status")
    version_info: Dict[str, Any] = Field(..., description="Database version information")
    schema_info: Dict[str, Any] = Field(..., description="Schema information")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Status check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json
        return json.dumps(data)


class DatabaseTablesResponse(BaseModel):
    """Database tables response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    tables: List[Dict[str, Any]] = Field(..., description="List of database tables")
    total_tables: int = Field(..., description="Total number of tables")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json
        return json.dumps(data)


class DatabaseMigrationsResponse(BaseModel):
    """Database migrations response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    applied_migrations: List[Dict[str, Any]] = Field(..., description="Applied migrations")
    pending_migrations: List[Dict[str, Any]] = Field(..., description="Pending migrations")
    migration_status: str = Field(..., description="Overall migration status")
    last_migration: Optional[Dict[str, Any]] = Field(default=None, description="Last migration")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json
        return json.dumps(data)


class DatabaseAnalysisResponse(BaseModel):
    """Database analysis response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    table_stats: List[Dict[str, Any]] = Field(..., description="Table statistics")
    index_analysis: List[Dict[str, Any]] = Field(..., description="Index analysis")
    performance_insights: Dict[str, Any] = Field(..., description="Performance insights")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Analysis timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json
        return json.dumps(data)


class DatabaseQueryResponse(BaseModel):
    """Database query execution response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Query execution success status")
    query: str = Field(..., description="Executed query")
    result_type: str = Field(..., description="Type of query result")
    rows_affected: Optional[int] = Field(default=None, description="Number of rows affected")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Query results")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Execution timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                # Use proper ISO format - if it's UTC, replace +00:00 with Z for consistency
                iso_string = data["timestamp"].isoformat()
                if iso_string.endswith("+00:00"):
                    iso_string = iso_string[:-6] + "Z"
                data["timestamp"] = iso_string
        import json
        return json.dumps(data)


# --- User Statistics Response Models ---


class UserStatisticsResponse(BaseModel):
    """User statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="User statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


# --- Search and Export Response Models ---


class SearchResponse(BaseModel):
    """Search response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Search operation success status")
    data: Dict[str, Any] = Field(..., description="Search results data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


class RegistryStatsResponse(BaseModel):
    """Registry statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Registry statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)


class ConversationStatsResponse(BaseModel):
    """Conversation statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Conversation statistics data")

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        import json
        return json.dumps(data)