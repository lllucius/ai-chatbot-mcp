"""Pydantic response schemas for search API endpoints.

This module provides response models for all search-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchSuggestion(BaseModel):
    """Individual search suggestion."""

    text: str = Field(..., description="Suggested search text")
    score: float = Field(..., description="Relevance score for suggestion")
    category: Optional[str] = Field(default=None, description="Suggestion category")


class SearchSuggestionData(BaseModel):
    """Search suggestions data."""

    query: str = Field(..., description="Original query that suggestions are based on")
    suggestions: List[str] = Field(
        default_factory=list, description="List of search suggestions"
    )

