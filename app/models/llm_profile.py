"Llm_Profile model definitions and database schemas."

from datetime import datetime
from typing import Optional
from sqlalchemy import JSON, Boolean, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModelDB


class LLMProfile(BaseModelDB):
    "LLMProfile class for specialized functionality."

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
    __table_args__ = (
        Index("idx_llm_profiles_default", "is_default"),
        Index("idx_llm_profiles_active", "is_active"),
        Index("idx_llm_profiles_usage_count", "usage_count"),
        Index("idx_llm_profiles_last_used", "last_used_at"),
    )

    def record_usage(self):
        "Record Usage operation."
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def to_openai_params(self) -> dict:
        "To Openai Params operation."
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
        if self.other_params:
            for key, value in self.other_params.items():
                if key not in params:
                    params[key] = value
        return params

    def to_dict(self) -> dict:
        "To Dict operation."
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
        "Return detailed object representation."
        default_marker = " (default)" if self.is_default else ""
        status = "active" if self.is_active else "inactive"
        return f"<LLMProfile(name='{self.name}', status='{status}', usage={self.usage_count}{default_marker})>"
