"""Pydantic response schemas for prompt registry API endpoints.

This module provides response models for all prompt-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptCategoryInfo(BaseModel):
    """Prompt category information."""

    name: str = Field(..., description="Category name")
    count: int = Field(..., description="Number of prompts in category")
    description: Optional[str] = Field(default=None, description="Category description")


class PromptStatisticsData(BaseModel):
    """Prompt statistics data."""

    total_prompts: int = Field(..., description="Total number of prompts")
    active_prompts: int = Field(..., description="Number of active prompts")
    default_prompt: str = Field(..., description="Name of default prompt")
    usage_stats: Dict[str, Any] = Field(default_factory=dict, description="Usage statistics")
    most_used: List[Dict[str, Any]] = Field(default_factory=list, description="Most frequently used prompts")
    recently_used: List[Dict[str, Any]] = Field(default_factory=list, description="Most frequently used prompts")
    categories: List[PromptCategoryInfo] = Field(default_factory=list, description="Category breakdown")
    total_tags: int = Field(..., description="Total number of tags")


class PromptCategoriesData(BaseModel):
    """Prompt categories and tags data."""

    categories: List[str] = Field(default_factory=list, description="Available prompt categories")
    tags: List[str] = Field(default_factory=list, description="Available prompt tags")


