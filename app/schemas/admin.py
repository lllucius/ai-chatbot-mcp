"""
Admin-specific schemas for API endpoints.

This module provides Pydantic schemas for administrative endpoints including
tools, tasks, profiles, prompts, and other management functionality.
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from ..utils.timestamp import utcnow

# --- Tools Response Models ---


class ToolResponse(BaseModel):
    """Tool response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    tool_name: str = Field(..., description="Tool name")
    tool_info: Dict[str, Any] = Field(..., description="Tool information")
    server_info: Dict[str, Any] = Field(..., description="Server information")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Response timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ToolTestResponse(BaseModel):
    """Tool test execution response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Test execution success status")
    tool_name: str = Field(..., description="Tool name")
    test_result: Dict[str, Any] = Field(..., description="Test execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Test execution timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ServerStatusResponse(BaseModel):
    """Server status response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    servers: List[Dict[str, Any]] = Field(..., description="Server status information")
    total_servers: int = Field(..., description="Total number of servers")
    healthy_servers: int = Field(..., description="Number of healthy servers")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Status check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- Tasks Response Models ---


class TaskStatusResponse(BaseModel):
    """Task status response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    task_system: str = Field(..., description="Task system type")
    broker_status: Dict[str, Any] = Field(..., description="Broker status information")
    workers: List[Dict[str, Any]] = Field(..., description="Worker information")
    queues: List[Dict[str, Any]] = Field(..., description="Queue information")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Status check timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class WorkersResponse(BaseModel):
    """Workers response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    workers: List[Dict[str, Any]] = Field(..., description="Worker information")
    total_workers: int = Field(..., description="Total number of workers")
    active_workers: int = Field(..., description="Number of active workers")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class QueueResponse(BaseModel):
    """Queue response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    queues: List[Dict[str, Any]] = Field(..., description="Queue information")
    total_tasks: int = Field(..., description="Total number of tasks")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ActiveTasksResponse(BaseModel):
    """Active tasks response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    active_tasks: List[Dict[str, Any]] = Field(..., description="Active task information")
    total_active: int = Field(..., description="Total number of active tasks")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Query timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class TaskStatsResponse(BaseModel):
    """Task statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    stats: Dict[str, Any] = Field(..., description="Task statistics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Statistics timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class TaskMonitorResponse(BaseModel):
    """Task monitor response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    monitoring_data: Dict[str, Any] = Field(..., description="Task monitoring data")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Monitor timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- Profiles Response Models ---


class ProfileParametersResponse(BaseModel):
    """Profile parameters response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    profile_name: str = Field(..., description="Profile name")
    parameters: Dict[str, Any] = Field(..., description="Profile parameters")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Response timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ProfileStatsResponse(BaseModel):
    """Profile statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    stats: Dict[str, Any] = Field(..., description="Profile statistics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Statistics timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class ProfileValidationResponse(BaseModel):
    """Profile validation response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Validation success status")
    valid: bool = Field(..., description="Whether the profile is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    validated_parameters: Dict[str, Any] = Field(..., description="Validated parameters")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Validation timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- Prompts Response Models ---


class PromptCategoriesResponse(BaseModel):
    """Prompt categories response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    categories: List[Dict[str, Any]] = Field(..., description="Prompt categories")
    total_categories: int = Field(..., description="Total number of categories")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Response timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class PromptStatsResponse(BaseModel):
    """Prompt statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    stats: Dict[str, Any] = Field(..., description="Prompt statistics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Statistics timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


# --- Documents Response Models ---


class DocumentStatsResponse(BaseModel):
    """Document statistics response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Operation success status")
    stats: Dict[str, Any] = Field(..., description="Document statistics")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Statistics timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)


class AdvancedSearchResponse(BaseModel):
    """Advanced search response schema."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    success: bool = Field(..., description="Search operation success status")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_metadata: Dict[str, Any] = Field(..., description="Search metadata")
    timestamp: datetime = Field(
        default_factory=utcnow, description="Search timestamp"
    )

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        if "timestamp" in data and data["timestamp"] is not None:
            if isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat() + "Z"
        import json
        return json.dumps(data)
