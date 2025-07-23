"""
MCP Tool model for tracking individual tools and their usage statistics.

This module defines the MCPTool model for managing tools provided by MCP servers,
their configuration, and usage analytics.

Current Date and Time (UTC): 2025-07-23 03:25:00
Current User: lllucius / assistant
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .mcp_server import MCPServer


class MCPTool(BaseModelDB):
    """
    MCP Tool model for tracking individual tools and usage statistics.

    Attributes:
        name: Full name of the tool (server_toolname)
        original_name: Original tool name from the server
        server_id: Foreign key to the MCP server
        description: Tool description
        parameters: Tool parameters schema as JSON
        is_enabled: Whether the tool is enabled
        usage_count: Total number of times the tool has been called
        last_used_at: Timestamp of last usage
        success_count: Number of successful executions
        error_count: Number of failed executions
        average_duration_ms: Average execution duration in milliseconds
        server: Related MCP server
    """

    __tablename__ = "mcp_tools"

    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True,
        doc="Full name of the tool (server_toolname)"
    )
    original_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="Original tool name from the server"
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False,
        doc="Foreign key to the MCP server"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="Tool description"
    )
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        doc="Tool parameters schema"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
        doc="Whether the tool is enabled"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        doc="Total number of times the tool has been called"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp of last usage"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        doc="Number of successful executions"
    )
    error_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        doc="Number of failed executions"
    )
    average_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="Average execution duration in milliseconds"
    )

    # Relationships
    server: Mapped["MCPServer"] = relationship(
        "MCPServer", back_populates="tools"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_mcp_tools_server_id", "server_id"),
        Index("idx_mcp_tools_enabled", "is_enabled"),
        Index("idx_mcp_tools_usage_count", "usage_count"),
        Index("idx_mcp_tools_last_used", "last_used_at"),
    )

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the tool."""
        total_calls = self.success_count + self.error_count
        if total_calls == 0:
            return 0.0
        return (self.success_count / total_calls) * 100.0

    def record_usage(self, success: bool, duration_ms: Optional[int] = None):
        """Record a tool usage event."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            
        if duration_ms is not None:
            if self.average_duration_ms is None:
                self.average_duration_ms = duration_ms
            else:
                # Running average calculation
                total_duration = self.average_duration_ms * (self.usage_count - 1)
                self.average_duration_ms = int((total_duration + duration_ms) / self.usage_count)

    def __repr__(self) -> str:
        """Return string representation of MCPTool model."""
        status = "enabled" if self.is_enabled else "disabled"
        return f"<MCPTool(name='{self.name}', status='{status}', usage={self.usage_count})>"