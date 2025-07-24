"""
Tool calling related schemas and enums.

This module provides schemas and enums for tool calling functionality,
including different modes for handling tool call results.

"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BaseSchema


class ToolHandlingMode(str, Enum):
    """
    Enum for different tool call result handling modes.

    - RETURN_RESULTS: Return tool call results as content without further AI processing
    - COMPLETE_WITH_RESULTS: Feed tool results back to AI for final completion
    """

    RETURN_RESULTS = "return_results"
    COMPLETE_WITH_RESULTS = "complete_with_results"


class ToolCallResult(BaseSchema):
    """Schema for individual tool call result."""

    tool_call_id: str = Field(..., description="ID of the tool call")
    tool_name: str = Field(..., description="Name of the tool that was called")
    success: bool = Field(..., description="Whether the tool call was successful")
    content: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool result content"
    )
    error: Optional[str] = Field(None, description="Error message if tool call failed")
    provider: Optional[str] = Field(
        None, description="Tool provider (fastmcp, openai, etc.)"
    )
    execution_time_ms: Optional[float] = Field(
        None, description="Execution time in milliseconds"
    )


class ToolCallSummary(BaseSchema):
    """Schema for tool call execution summary."""

    total_calls: int = Field(..., description="Total number of tool calls made")
    successful_calls: int = Field(..., description="Number of successful tool calls")
    failed_calls: int = Field(..., description="Number of failed tool calls")
    total_execution_time_ms: float = Field(
        ..., description="Total execution time in milliseconds"
    )
    results: List[ToolCallResult] = Field(
        default_factory=list, description="Individual tool call results"
    )
