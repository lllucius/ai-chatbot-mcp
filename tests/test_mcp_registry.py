"""
Unit tests for MCP registry functionality.

These tests cover MCP server and tool management including
registration, enablement, and usage tracking.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.mcp_registry import MCPRegistryService


class TestMCPRegistryService:
    """Test MCP registry service functionality."""

    @pytest.mark.asyncio
    async def test_create_server(self):
        """Test creating an MCP server registration."""
        with patch("app.services.mcp_registry.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            server = await MCPRegistryService.create_server(
                name="test_server",
                url="http://localhost:9000/mcp",
                description="Test server",
                transport="http",
                timeout=30,
            )

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_disable_server(self):
        """Test enabling and disabling servers."""
        with patch("app.services.mcp_registry.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock server exists
            mock_db.execute.return_value.scalar_one_or_none.return_value = AsyncMock()

            # Test enable
            result = await MCPRegistryService.enable_server("test_server")
            assert result is True

            # Test disable
            result = await MCPRegistryService.disable_server("test_server")
            assert result is True

    @pytest.mark.asyncio
    async def test_register_tool(self):
        """Test registering a tool for an MCP server."""
        with patch("app.services.mcp_registry.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock server exists
            mock_server = AsyncMock()
            mock_server.id = "server-123"
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_server,  # Server lookup
                None,  # Tool doesn't exist
            ]

            tool = await MCPRegistryService.register_tool(
                server_name="test_server",
                tool_name="test_server_tool",
                original_name="tool",
                description="Test tool",
                parameters={"type": "object"},
            )

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_tool_usage(self):
        """Test recording tool usage statistics."""
        with patch("app.services.mcp_registry.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock tool exists
            mock_tool = AsyncMock()
            mock_tool.usage_count = 5
            mock_tool.success_count = 4
            mock_tool.error_count = 1
            mock_tool.average_duration_ms = 100
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_tool

            result = await MCPRegistryService.record_tool_usage(
                tool_name="test_tool", success=True, duration_ms=150
            )

            assert result is True
            mock_tool.record_usage.assert_called_once_with(True, 150)
            mock_db.commit.assert_called_once()


class TestMCPToolUsageTracking:
    """Test MCP tool usage tracking functionality."""

    def test_tool_success_rate_calculation(self):
        """Test tool success rate calculation."""
        from app.models.mcp_tool import MCPTool

        tool = MCPTool(
            name="test_tool",
            original_name="tool",
            server_id="server-123",
            success_count=8,
            error_count=2,
        )

        assert tool.success_rate == 80.0

    def test_tool_success_rate_no_usage(self):
        """Test tool success rate with no usage."""
        from app.models.mcp_tool import MCPTool

        tool = MCPTool(
            name="test_tool",
            original_name="tool",
            server_id="server-123",
            success_count=0,
            error_count=0,
        )

        assert tool.success_rate == 0.0

    def test_tool_record_usage(self):
        """Test recording tool usage."""

        from app.models.mcp_tool import MCPTool

        tool = MCPTool(
            name="test_tool",
            original_name="tool",
            server_id="server-123",
            usage_count=0,
            success_count=0,
            error_count=0,
        )

        # Record successful usage
        tool.record_usage(success=True, duration_ms=100)

        assert tool.usage_count == 1
        assert tool.success_count == 1
        assert tool.error_count == 0
        assert tool.average_duration_ms == 100
        assert tool.last_used_at is not None

        # Record failed usage
        tool.record_usage(success=False, duration_ms=200)

        assert tool.usage_count == 2
        assert tool.success_count == 1
        assert tool.error_count == 1
        assert tool.average_duration_ms == 150  # (100 + 200) / 2
