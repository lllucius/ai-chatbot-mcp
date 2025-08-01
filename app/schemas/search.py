"""
Search-related Pydantic schemas.

This module provides schemas for document and chunk search, similarity,
suggestions, and search history.
All fields have an explicit 'description' argument.
"""

from typing import List

from pydantic import BaseModel, Field


class SearchSuggestionResponse(BaseModel):
    """Response schema for search suggestions."""
    success: bool = Field(..., description="Whether the request succeeded")
    message: str = Field(..., description="Status message")
    query: str = Field(..., description="Original query string")
    suggestions: List[str] = Field(..., description="List of suggested queries")


class SearchHistoryItem(BaseModel):
    """Schema for a single search history record."""
    query: str = Field(..., description="Search query string")
    timestamp: str = Field(..., description="When the search was performed (ISO-8601)")
    results_count: int = Field(..., description="Number of results")
    algorithm: str = Field(..., description="Algorithm used")


class SearchHistoryResponse(BaseModel):
    """Response schema for search history."""
    success: bool = Field(..., description="Whether the request succeeded")
    message: str = Field(..., description="Status message")
    history: List[SearchHistoryItem] = Field(..., description="List of search history items")
    total: int = Field(..., description="Total number of history items")


class SearchClearHistoryResponse(BaseModel):
    """Response schema for clearing search history."""
    success: bool = Field(..., description="Whether the request succeeded")
    message: str = Field(..., description="Status message")