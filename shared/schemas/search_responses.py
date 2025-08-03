"""
Pydantic response schemas for search API endpoints.

This module provides response models for all search-related endpoints that currently
return raw dictionaries, ensuring type safety and proper API documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseModelSchema


class SearchSuggestion(BaseModel):
    """Individual search suggestion."""
    
    text: str = Field(..., description="Suggested search text")
    score: float = Field(..., description="Relevance score for suggestion")
    category: Optional[str] = Field(default=None, description="Suggestion category")


class SearchSuggestionData(BaseModel):
    """Search suggestions data."""
    
    suggestions: List[SearchSuggestion] = Field(default_factory=list, description="List of search suggestions")
    query: str = Field(..., description="Original query that suggestions are based on")
    total_suggestions: int = Field(..., description="Total number of suggestions")
    timestamp: str = Field(..., description="Suggestions timestamp")


class SearchHistoryEntry(BaseModel):
    """Individual search history entry."""
    
    query: str = Field(..., description="Search query")
    timestamp: str = Field(..., description="When the search was performed")
    results_count: int = Field(..., description="Number of results returned")
    algorithm_used: str = Field(..., description="Search algorithm that was used")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")


class SearchHistoryData(BaseModel):
    """Search history data."""
    
    history: List[SearchHistoryEntry] = Field(default_factory=list, description="List of recent searches")
    total_searches: int = Field(..., description="Total number of searches by user")
    most_common_queries: List[str] = Field(default_factory=list, description="Most frequently searched queries")
    timestamp: str = Field(..., description="History data timestamp")