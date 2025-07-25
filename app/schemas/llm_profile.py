"""
LLM Profile registry schemas for API requests and responses.

This module provides Pydantic schemas for LLM profile management
including creation, updates, and response models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMProfileResponse(BaseModel):
    """LLM profile registry response model."""

    name: str = Field(..., description="Unique profile name")
    title: str = Field(..., description="Human-readable title")
    description: Optional[str] = Field(None, description="Profile description")
    model_name: str = Field(..., description="OpenAI model name")
    parameters: Dict[str, Any] = Field(..., description="Model parameters")
    is_default: bool = Field(False, description="Whether this is the default profile")
    is_active: bool = Field(True, description="Whether profile is active")
    usage_count: int = Field(0, description="How many times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class LLMProfileCreate(BaseModel):
    """Create LLM profile request model."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique profile name")
    title: str = Field(..., min_length=1, max_length=200, description="Human-readable title")
    description: Optional[str] = Field(None, max_length=1000, description="Profile description")
    model_name: str = Field(..., description="OpenAI model name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    is_active: bool = Field(True, description="Whether profile is active")


class LLMProfileUpdate(BaseModel):
    """Update LLM profile request model."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Human-readable title")
    description: Optional[str] = Field(None, max_length=1000, description="Profile description")
    model_name: Optional[str] = Field(None, description="OpenAI model name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Model parameters")
    is_active: Optional[bool] = Field(None, description="Whether profile is active")


class LLMProfileListResponse(BaseModel):
    """Response model for listing LLM profiles."""

    profiles: List[LLMProfileResponse] = Field(..., description="List of profiles")
    total: int = Field(..., description="Total number of profiles")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    model_config = {"from_attributes": True}