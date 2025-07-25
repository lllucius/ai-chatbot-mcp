"""
Prompt registry schemas for API requests and responses.

This module provides Pydantic schemas for prompt management
including creation, updates, and response models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptResponse(BaseModel):
    """Prompt registry response model."""

    name: str = Field(..., description="Unique prompt name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    content: str = Field(..., description="Prompt template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_active: bool = Field(True, description="Whether prompt is active")
    is_default: bool = Field(False, description="Whether this is the default prompt")
    usage_count: int = Field(0, description="How many times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class PromptCreate(BaseModel):
    """Create prompt request model."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique prompt name")
    title: str = Field(..., min_length=1, max_length=200, description="Human-readable title")
    description: Optional[str] = Field(None, max_length=1000, description="Prompt description")
    category: Optional[str] = Field(None, max_length=100, description="Prompt category")
    content: str = Field(..., min_length=1, description="Prompt template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_active: bool = Field(True, description="Whether prompt is active")


class PromptUpdate(BaseModel):
    """Update prompt request model."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Human-readable title")
    description: Optional[str] = Field(None, max_length=1000, description="Prompt description")
    category: Optional[str] = Field(None, max_length=100, description="Prompt category")
    content: Optional[str] = Field(None, min_length=1, description="Prompt template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_active: Optional[bool] = Field(None, description="Whether prompt is active")


class PromptListResponse(BaseModel):
    """Response model for listing prompts."""

    prompts: List[PromptResponse] = Field(..., description="List of prompts")
    total: int = Field(..., description="Total number of prompts")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    model_config = {"from_attributes": True}