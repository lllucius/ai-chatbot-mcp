"""Pydantic response schemas for database API endpoints.

This module provides response models for all database-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .admin_responses import utcnow


class DatabaseUpgradeResult(BaseModel):
    output: str = Field(..., description="Output from alembic upgrade command")
    revision: str = Field(..., description="Target revision")


class DatabaseDowngradeResult(BaseModel):
    output: str = Field(..., description="Output from alembic downgrade command")
    revision: str = Field(..., description="Target revision")


class DatabaseBackupResult(BaseModel):
    output_file: str = Field(..., description="Path to backup file created")
    file_size: str = Field(..., description="Size of backup file")
    schema_only: bool = Field(..., description="Whether only schema was backed up")


class DatabaseRestoreResult(BaseModel):
    message: str = Field(..., description="Status message")
    backup_file: str = Field(..., description="Restored backup file path")


class VacuumResult(BaseModel):
    message: str = Field(..., description="Status message")
    analyze: bool = Field(..., description="Whether ANALYZE was run after VACUUM")


class DatabaseStatusResponse(BaseModel):
    """Database status response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    connection_status: str = Field(..., description="Database connection status")
    version_info: Dict[str, Any] = Field(
        ..., description="Database version information"
    )
    schema_info: Dict[str, Any] = Field(..., description="Schema information")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Status check timestamp"
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
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
    timestamp: datetime = Field(default_factory=utcnow, description="Query timestamp")

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
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
    applied_migrations: List[Dict[str, Any]] = Field(
        ..., description="Applied migrations"
    )
    pending_migrations: List[Dict[str, Any]] = Field(
        ..., description="Pending migrations"
    )
    migration_status: str = Field(..., description="Overall migration status")
    last_migration: Optional[Dict[str, Any]] = Field(
        default=None, description="Last migration"
    )
    timestamp: datetime = Field(default_factory=utcnow, description="Query timestamp")

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
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
    performance_insights: Dict[str, Any] = Field(
        ..., description="Performance insights"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    timestamp: datetime = Field(
        default_factory=utcnow, description="Analysis timestamp"
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
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
    rows_affected: Optional[int] = Field(
        default=None, description="Number of rows affected"
    )
    execution_time_ms: float = Field(
        ..., description="Query execution time in milliseconds"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Query results"
    )
    timestamp: datetime = Field(
        default_factory=utcnow, description="Execution timestamp"
    )

    def model_dump_json(self, **kwargs):
        """Serialize model with ISO format timestamp handling."""
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
