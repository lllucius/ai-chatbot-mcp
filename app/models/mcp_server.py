"""
MCP Server registry model for managing MCP server configurations.

This module defines the MCPServer model for tracking configured MCP servers,
their status, and configuration details.

Current Date and Time (UTC): 2025-07-23 03:25:00
Current User: lllucius / assistant
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelDB

if TYPE_CHECKING:
    from .mcp_tool import MCPTool


class MCPServer(BaseModelDB):
    """
    MCP Server registry model for managing server configurations.

    Attributes:
        name: Unique name/identifier for the server
        url: Connection URL for the server
        description: Optional description of the server
        transport: Transport type (http, stdio, etc.)
        timeout: Connection timeout in seconds
        config: Additional server configuration as JSON
        is_enabled: Whether the server is enabled
        is_connected: Current connection status
        last_connected_at: Timestamp of last successful connection
        connection_errors: Count of recent connection errors
        tools: Related tools provided by this server
    """

    __tablename__ = "mcp_servers"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        doc="Unique name for the MCP server"
    )
    url: Mapped[str] = mapped_column(
        String(500), nullable=False,
        doc="Connection URL for the server"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="Optional description of the server"
    )
    transport: Mapped[str] = mapped_column(
        String(50), nullable=False, default="http",
        doc="Transport protocol (http, stdio, etc.)"
    )
    timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30,
        doc="Connection timeout in seconds"
    )
    config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        doc="Additional server configuration"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
        doc="Whether the server is enabled"
    )
    is_connected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True,
        doc="Current connection status"
    )
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp of last successful connection"
    )
    connection_errors: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        doc="Count of recent connection errors"
    )

    # Relationships
    tools: Mapped[List["MCPTool"]] = relationship(
        "MCPTool", back_populates="server", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return string representation of MCPServer model."""
        status = "enabled" if self.is_enabled else "disabled"
        connected = "connected" if self.is_connected else "disconnected"
        return f"<MCPServer(name='{self.name}', status='{status}', {connected})>"