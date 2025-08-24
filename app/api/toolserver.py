"""Tool Server Management API endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_mcp_service
from app.models.user import User
from app.services.mcp_service import MCPService
from app.utils.api_errors import handle_api_errors, log_api_call
from shared.schemas.common import APIResponse, PaginatedResponse, PaginationParams
from shared.schemas.mcp import MCPConnectionTestSchema, MCPServerSchema

router = APIRouter(tags=["tool-servers"])


# Create a simple ToolServerResponse model for compatibility with the problem statement
class ToolServerResponse(MCPServerSchema):
    """Tool server response schema."""
    pass


@router.get("/servers")
@handle_api_errors("Failed to retrieve tool servers")
async def get_servers(
    current_user: User = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedResponse[ToolServerResponse]]:
    """Get list of all tool servers with pagination."""
    log_api_call("get_servers", user_id=str(current_user.id))
    
    # Get servers from MCP service
    servers = await mcp_service.list_servers()
    
    # Convert to response format
    server_responses = [ToolServerResponse.model_validate(server) for server in servers]
    
    # Create paginated response
    payload = PaginatedResponse(
        items=server_responses,
        pagination=PaginationParams(
            total=len(server_responses),
            page=1,
            per_page=len(server_responses),
        ),
    )
    
    return APIResponse[PaginatedResponse[ToolServerResponse]](
        success=True,
        message="Tool servers retrieved successfully",
        data=payload,
    )


@router.get("/tools/all")
@handle_api_errors("Failed to retrieve all tools")
async def get_all_tools(
    current_user: User = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[PaginatedResponse[Dict]]:
    """Get list of all available tools from all servers with pagination."""
    log_api_call("get_all_tools", user_id=str(current_user.id))
    
    # Get tools from MCP service
    tools_response = await mcp_service.list_tools()
    
    # Convert tools to dict format for compatibility
    tools_dict_list = []
    for tool in tools_response.available_tools:
        tool_dict = {
            "name": tool.name,
            "original_name": tool.original_name,
            "description": tool.description,
            "parameters": tool.parameters,
            "is_enabled": tool.is_enabled,
            "usage_count": tool.usage_count,
            "success_rate": tool.success_rate,
            "server_name": tool.server.name if tool.server else None,
        }
        tools_dict_list.append(tool_dict)
    
    # Create paginated response
    payload = PaginatedResponse(
        items=tools_dict_list,
        pagination=PaginationParams(
            total=len(tools_dict_list),
            page=1,
            per_page=len(tools_dict_list),
        ),
    )
    
    return APIResponse[PaginatedResponse[Dict]](
        success=True,
        message="All tools retrieved successfully",
        data=payload,
    )


@router.post("/servers/{server_id}/test-connectivity")
@handle_api_errors("Failed to test server connectivity")
async def test_server_connectivity(
    server_id: str = Path(..., description="Server ID to test"),
    current_user: User = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service),
) -> APIResponse[Dict]:
    """Test connectivity to a specific tool server."""
    log_api_call("test_server_connectivity", user_id=str(current_user.id), server_id=server_id)
    
    # Test server connectivity
    test_result = await mcp_service.test_server_connection(server_id)
    
    # Convert to dict format
    result_dict = {
        "server_id": server_id,
        "connected": test_result.connected,
        "response_time": test_result.response_time,
        "server_version": test_result.server_version,
        "capabilities": test_result.capabilities,
        "tools_available": test_result.tools_available,
        "error": test_result.error,
        "tested_at": test_result.tested_at.isoformat() if test_result.tested_at else None,
    }
    
    return APIResponse[Dict](
        success=test_result.connected,
        message="Server connectivity test completed" if test_result.connected else f"Server connectivity test failed: {test_result.error}",
        data=result_dict,
    )