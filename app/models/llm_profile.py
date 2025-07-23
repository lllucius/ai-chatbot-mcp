"""
LLM Profile model for managing LLM tuning parameter configurations.

This module defines the LLMProfile model for storing and managing
different parameter profiles for language model interactions.

Current Date and Time (UTC): 2025-07-23 03:25:00
Current User: lllucius / assistant
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModelDB


class LLMProfile(BaseModelDB):
    """
    LLM Profile model for managing language model parameter configurations.

    Attributes:
        name: Unique name/identifier for the profile
        title: Display title for the profile
        description: Optional description of the profile's purpose
        is_default: Whether this is the default profile
        is_active: Whether the profile is active/available
        usage_count: Number of times the profile has been used
        last_used_at: Timestamp of last usage

        # Core LLM Parameters
        temperature: Controls randomness in generation (0.0-2.0)
        top_p: Nucleus sampling parameter (0.0-1.0)
        top_k: Top-k sampling parameter
        repeat_penalty: Repetition penalty (typically around 1.0)
        max_tokens: Maximum tokens to generate
        max_new_tokens: Maximum new tokens to generate (alternative to max_tokens)
        context_length: Maximum context length
        presence_penalty: Presence penalty (-2.0 to 2.0)
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        stop: Stop sequences as JSON list

        # Additional parameters
        other_params: Additional model-specific parameters as JSON
    """

    __tablename__ = "llm_profiles"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique name/identifier for the profile",
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Display title for the profile"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Optional description of the profile's purpose"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this is the default profile",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the profile is active/available",
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times the profile has been used",
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="Timestamp of last usage"
    )

    # Core LLM Parameters
    temperature: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Controls randomness in generation (0.0-2.0)"
    )
    top_p: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Nucleus sampling parameter (0.0-1.0)"
    )
    top_k: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Top-k sampling parameter"
    )
    repeat_penalty: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Repetition penalty (typically around 1.0)"
    )
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Maximum tokens to generate"
    )
    max_new_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Maximum new tokens to generate"
    )
    context_length: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Maximum context length"
    )
    presence_penalty: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Presence penalty (-2.0 to 2.0)"
    )
    frequency_penalty: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Frequency penalty (-2.0 to 2.0)"
    )
    stop: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, doc="Stop sequences as JSON list"
    )
    other_params: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, doc="Additional model-specific parameters"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_llm_profiles_default", "is_default"),
        Index("idx_llm_profiles_active", "is_active"),
        Index("idx_llm_profiles_usage_count", "usage_count"),
        Index("idx_llm_profiles_last_used", "last_used_at"),
    )

    def record_usage(self):
        """Record a profile usage event."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def to_openai_params(self) -> dict:
        """
        Convert LLM profile to OpenAI API parameters dictionary.

        Transforms the profile settings into a format compatible with OpenAI's
        chat completion API. Only includes parameters that are not None to allow
        OpenAI's defaults to take effect for unspecified parameters.

        Returns:
            dict: Dictionary of OpenAI API parameters with the following possible keys:
                - temperature: Controls randomness (0.0-2.0)
                - top_p: Controls nucleus sampling (0.0-1.0)
                - max_tokens: Maximum tokens to generate
                - presence_penalty: Penalty for token presence (-2.0-2.0)
                - frequency_penalty: Penalty for token frequency (-2.0-2.0)
                - stop: List of stop sequences

        Example:
            >>> profile = LLMProfile(temperature=0.7, max_tokens=1000)
            >>> params = profile.to_openai_params()
            >>> params
            {"temperature": 0.7, "max_tokens": 1000}
        """
        params = {}

        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.stop is not None:
            params["stop"] = self.stop

        # Add other parameters
        if self.other_params:
            for key, value in self.other_params.items():
                if key not in params:  # Don't override existing parameters
                    params[key] = value

        return params

    def to_dict(self) -> dict:
        """
        Convert profile to complete dictionary representation.

        Creates a comprehensive dictionary containing all profile parameters,
        metadata, and usage statistics. Useful for JSON serialization,
        API responses, and profile export/import operations.

        Returns:
            dict: Complete profile data including:
                - Basic info: name, title, description
                - Status flags: is_default, is_active
                - LLM parameters: temperature, top_p, max_tokens, etc.
                - Penalties: presence_penalty, frequency_penalty
                - Metadata: created_at, updated_at, usage stats
                - Additional custom parameters from other_params

        Example:
            >>> profile = LLMProfile(name="creative", temperature=0.8)
            >>> data = profile.to_dict()
            >>> data["name"]
            "creative"
            >>> data["temperature"]
            0.8
        """
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "max_tokens": self.max_tokens,
            "max_new_tokens": self.max_new_tokens,
            "context_length": self.context_length,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "other_params": self.other_params,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at,
        }

    def __repr__(self) -> str:
        """Return string representation of LLMProfile model."""
        default_marker = " (default)" if self.is_default else ""
        status = "active" if self.is_active else "inactive"
        return f"<LLMProfile(name='{self.name}', status='{status}', usage={self.usage_count}{default_marker})>"
