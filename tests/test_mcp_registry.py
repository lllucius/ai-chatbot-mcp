"""
Unit tests for MCP registry functionality.

These tests cover MCP server and tool management including
registration, enablement, and usage tracking using the refactored
dependency injection patterns and Pydantic schemas.
"""

from unittest.mock import AsyncMock, patch
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mcp import MCPServerCreateSchema, MCPToolCreateSchema, MCPListFiltersSchema
from app.services.mcp_registry import MCPRegistryService


class TestMCPRegistryService:
    """Test MCP registry service functionality with dependency injection."""

    @pytest.mark.asyncio
    async def test_create_server(self):
        """Test creating an MCP server registration."""
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock server model
        mock_server = AsyncMock()
        mock_server.id = uuid.uuid4()
        mock_server.name = "test_server"
        mock_server.url = "http://localhost:9000/mcp"
        
        registry = MCPRegistryService(mock_db)
        
        server_data = MCPServerCreateSchema(
            name="test_server",
            url="http://localhost:9000/mcp",
            description="Test server",
            transport="http",
            timeout=30,
        )

        with patch("app.services.mcp_registry.MCPServer") as mock_server_class:
            mock_server_class.return_value = mock_server
            
            result = await registry.create_server(server_data, auto_discover=False)

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_disable_server(self):
        """Test enabling and disabling servers."""
        mock_db = AsyncMock(spec=AsyncSession)
        registry = MCPRegistryService(mock_db)
        
        # Mock existing server
        mock_server = AsyncMock()
        mock_server.name = "test_server"
        mock_server.is_enabled = False
        
        # Mock the get_server method to return the server
        with patch.object(registry, 'get_server', return_value=mock_server):
            with patch.object(registry, 'update_server', return_value=mock_server) as mock_update:
                # Test enable
                result = await registry.enable_server("test_server", auto_discover=False)
                assert result is not None
                mock_update.assert_called()

                # Test disable
                result = await registry.disable_server("test_server")
                assert result is not None
                mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_register_tool(self):
        """Test registering a tool for an MCP server."""
        mock_db = AsyncMock(spec=AsyncSession)
        registry = MCPRegistryService(mock_db)

        # Mock server and tool
        mock_server = AsyncMock()
        mock_server.id = uuid.uuid4()
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            mock_server,  # Server lookup
            None,  # Tool doesn't exist
        ]

        tool_data = MCPToolCreateSchema(
            name="test_server_tool",
            original_name="tool",
            server_name="test_server",
            description="Test tool",
            parameters={"type": "object"},
        )

        with patch("app.services.mcp_registry.MCPTool") as mock_tool_class:
            mock_tool = AsyncMock()
            mock_tool_class.return_value = mock_tool
            
            result = await registry.register_tool(tool_data)

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_tool_usage(self):
        """Test recording tool usage statistics."""
        mock_db = AsyncMock(spec=AsyncSession)
        registry = MCPRegistryService(mock_db)

        # Mock tool exists
        mock_tool = AsyncMock()
        mock_tool.usage_count = 5
        mock_tool.success_count = 4
        mock_tool.error_count = 1
        mock_tool.average_duration_ms = 100
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_tool

        result = await registry.record_tool_usage(
            tool_name="test_tool", success=True, duration_ms=150
        )

        assert result is True
        mock_tool.record_usage.assert_called_once_with(True, 150)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_with_filters(self):
        """Test listing tools with filters."""
        mock_db = AsyncMock(spec=AsyncSession)
        registry = MCPRegistryService(mock_db)

        # Mock query result
        mock_result = AsyncMock()
        mock_tools = [AsyncMock() for _ in range(3)]
        mock_result.scalars.return_value.all.return_value = mock_tools
        mock_db.execute.return_value = mock_result

        filters = MCPListFiltersSchema(enabled_only=True, server_name="test_server")
        tools = await registry.list_tools(filters)

        # Verify query was executed
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_record_tool_usage(self):
        """Test batch recording of tool usage."""
        mock_db = AsyncMock(spec=AsyncSession)
        registry = MCPRegistryService(mock_db)

        usage_records = [
            {"tool_name": "tool1", "success": True, "duration_ms": 100},
            {"tool_name": "tool2", "success": False, "duration_ms": 200},
        ]

        with patch.object(registry, 'record_tool_usage', return_value=True) as mock_record:
            result = await registry.batch_record_tool_usage(usage_records)
            
            assert result == 2
            assert mock_record.call_count == 2


class TestMCPToolUsageTracking:
    """Test MCP tool usage tracking functionality."""

    def test_tool_success_rate_calculation(self):
        """Test tool success rate calculation."""
        from app.models.mcp_tool import MCPTool

        tool = MCPTool(
            name="test_tool",
            original_name="tool",
            server_id=uuid.uuid4(),
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
            server_id=uuid.uuid4(),
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
            server_id=uuid.uuid4(),
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


class TestMCPClientIntegration:
    """Test MCP client integration with refactored services."""

    @pytest.mark.asyncio
    async def test_client_initialization_with_registry(self):
        """Test client initializes correctly with registry service."""
        from app.services.mcp_client import FastMCPClientService
        
        mock_registry = AsyncMock()
        mock_registry.list_servers.return_value = []
        mock_registry.list_tools.return_value = []
        
        client = FastMCPClientService(registry_service=mock_registry)
        
        # Should handle empty registry gracefully
        await client.initialize()
        
        assert not client.is_initialized  # No servers to connect to

    @pytest.mark.asyncio
    async def test_client_tool_execution_with_schemas(self):
        """Test tool execution using Pydantic schemas."""
        from app.services.mcp_client import FastMCPClientService
        from app.schemas.mcp import MCPToolExecutionRequestSchema, MCPToolSchema, MCPServerSchema
        
        # Mock registry with tools
        mock_registry = AsyncMock()
        mock_server = MCPServerSchema(
            id=uuid.uuid4(),
            name="test_server",
            url="http://localhost:9000",
            transport="http",
            timeout=30,
            is_enabled=True,
            is_connected=True,
            connection_errors=0,
            tools_count=1,
            created_at=None,
            updated_at=None
        )
        
        mock_tool = MCPToolSchema(
            id=uuid.uuid4(),
            name="test_tool",
            original_name="tool",
            description="Test tool",
            parameters={"type": "object"},
            is_enabled=True,
            usage_count=0,
            success_count=0,
            error_count=0,
            success_rate=0.0,
            server=mock_server,
            created_at=None,
            updated_at=None
        )
        
        mock_registry.list_servers.return_value = [mock_server]
        mock_registry.list_tools.return_value = [mock_tool]
        
        client = FastMCPClientService(registry_service=mock_registry)
        
        # Mock the cache to include our tool
        client._cached_tools = {"test_tool": mock_tool}
        client._cached_servers = {"test_server": mock_server}
        client.is_initialized = True
        
        request = MCPToolExecutionRequestSchema(
            tool_name="test_tool",
            parameters={"test": "value"},
            record_usage=False
        )
        
        # Mock the actual FastMCP client
        mock_fastmcp_client = AsyncMock()
        mock_result = AsyncMock()
        mock_result.content = [AsyncMock(text="Test result")]
        mock_fastmcp_client.call_tool.return_value = mock_result
        mock_fastmcp_client.__aenter__ = AsyncMock(return_value=mock_fastmcp_client)
        mock_fastmcp_client.__aexit__ = AsyncMock(return_value=None)
        
        client.clients = {"test_server": mock_fastmcp_client}
        
        # Execute tool
        result = await client.call_tool(request)
        
        # Verify result
        assert result.success is True
        assert result.tool_name == "test_tool"
        assert result.server == "test_server"
        assert len(result.content) > 0
