"""Pydantic schemas for admin APIs.

This module provides administrative response schemas for system management,
monitoring, and administration functionality.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BaseModelSchema


# Task management schemas
class TaskStatusResponse(BaseModelSchema):
    """Task status response schema."""

    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task result")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class TaskStatsResponse(BaseModelSchema):
    """Task statistics response schema."""

    stats: Dict[str, Any] = Field(..., description="Task statistics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class QueueResponse(BaseModelSchema):
    """Queue status response schema."""

    queue: Dict[str, Any] = Field(..., description="Queue information")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class TaskMonitorResponse(BaseModelSchema):
    """Task monitoring response schema."""

    monitor: Dict[str, Any] = Field(..., description="Task monitoring data")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class WorkersResponse(BaseModelSchema):
    """Workers status response schema."""

    workers: List[Dict[str, Any]] = Field(..., description="Worker information")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


# Profile management schemas
class ProfileStatsResponse(BaseModelSchema):
    """Profile statistics response schema."""

    stats: Dict[str, Any] = Field(..., description="Profile statistics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


# Prompt management schemas
class PromptCategoriesResponse(BaseModelSchema):
    """Prompt categories response schema."""

    categories: List[str] = Field(..., description="Prompt categories")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class PromptStatsResponse(BaseModelSchema):
    """Prompt statistics response schema."""

    stats: Dict[str, Any] = Field(..., description="Prompt statistics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


# Document management schemas
class AdvancedSearchResponse(BaseModelSchema):
    """Advanced search response schema."""

    results: Dict[str, Any] = Field(..., description="Advanced search results")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")


class DocumentStatsResponse(BaseModelSchema):
    """Document statistics response schema."""

    stats: Dict[str, Any] = Field(..., description="Document statistics")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Response message")
