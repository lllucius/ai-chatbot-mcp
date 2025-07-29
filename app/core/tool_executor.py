"""
Unified tool execution system for centralizing tool calling logic.

This module provides a centralized interface for executing tools from both
FastMCP and OpenAI integrations, with consistent retry, fallback, error
handling, and caching behavior.

"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ExternalServiceError
from ..core.logging import get_api_logger
from ..schemas.mcp import MCPListFiltersSchema, MCPToolExecutionRequestSchema
from ..utils.api_errors import handle_api_errors
from ..utils.caching import api_response_cache, make_cache_key

logger = get_api_logger("tool_executor")


class ToolProvider(Enum):
    """Enum for different tool providers."""

    FASTMCP = "fastmcp"
    OPENAI = "openai"


@dataclass
class ToolCall:
    """Represents a tool call request."""

    id: str
    name: str
    arguments: Dict[str, Any]
    provider: Optional[ToolProvider] = None


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    tool_call_id: str
    success: bool
    content: List[Dict[str, Any]]
    error: Optional[str] = None
    provider: Optional[ToolProvider] = None
    execution_time_ms: Optional[float] = None


class ToolExecutionStrategy(ABC):
    """Abstract base class for tool execution strategies."""

    @abstractmethod
    async def execute_tool(self, tool_call: ToolCall, max_retries: int = 3, db_session: Optional[AsyncSession] = None) -> ToolResult:
        pass

    @abstractmethod
    async def get_available_tools(self, db_session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def health_check(self, db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        pass


class FastMCPToolStrategy(ToolExecutionStrategy):
    """Tool execution strategy for FastMCP tools."""

    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    async def execute_tool(self, tool_call: ToolCall, max_retries: int = 3, db_session: Optional[AsyncSession] = None) -> ToolResult:
        import time

        start_time = time.time()

        try:
            request = MCPToolExecutionRequestSchema(
                tool_name=tool_call.name,
                parameters=tool_call.arguments,
                record_usage=True
            )
            result = await self.mcp_client.call_tool(request, db_session)
            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_call_id=tool_call.id,
                success=result.success,
                content=result.content,
                provider=ToolProvider.FASTMCP,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"FastMCP tool execution failed: {e}")

            return ToolResult(
                tool_call_id=tool_call.id,
                success=False,
                content=[],
                error=str(e),
                provider=ToolProvider.FASTMCP,
                execution_time_ms=execution_time,
            )

    async def get_available_tools(self, db_session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        if not self.mcp_client or not self.mcp_client.is_initialized:
            return []

        filters = MCPListFiltersSchema(enabled_only=True)
        tools = await self.mcp_client.get_available_tools(filters, db_session)
        openai_tools = []
        for tool in tools:
            if tool.is_enabled and tool.server.is_enabled:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool from {tool.server.name}",
                        "parameters": tool.parameters or {"type": "object", "properties": {}}
                    }
                }
                openai_tools.append(openai_tool)
        return openai_tools

    async def health_check(self, db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not self.mcp_client:
            return {"status": "unavailable", "provider": "fastmcp"}
        health_result = await self.mcp_client.health_check(db_session)
        if hasattr(health_result, 'model_dump'):
            return health_result.model_dump()
        return health_result


class UnifiedToolExecutor:
    """
    Unified tool executor that centralizes all tool calling logic.

    This class provides a single interface for executing tools from different
    providers (FastMCP, OpenAI) with consistent retry, caching, and error
    handling behavior.
    """

    def __init__(self, mcp_client=None):
        self.strategies: Dict[ToolProvider, ToolExecutionStrategy] = {}
        self._initialized = False
        if mcp_client:
            self.strategies[ToolProvider.FASTMCP] = FastMCPToolStrategy(mcp_client)
            logger.info("FastMCP tool strategy initialized")
        self._initialized = True

    @handle_api_errors("Tool execution failed")
    async def execute_tool_call(
        self,
        tool_call: ToolCall,
        max_retries: int = 3,
        use_cache: bool = True,
        cache_ttl: int = 300,
        db_session: Optional[AsyncSession] = None,
    ) -> ToolResult:
        if not self._initialized:
            raise ExternalServiceError("Tool executor not initialized")

        cache_key = None
        if use_cache:
            cache_key = make_cache_key("tool_call", tool_call.name, tool_call.arguments)
            cached_result = await api_response_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for tool call: {tool_call.name}")
                return ToolResult(**cached_result)

        provider = tool_call.provider or self._determine_provider(tool_call.name)
        if provider not in self.strategies:
            raise ExternalServiceError(f"No strategy available for provider: {provider}")

        strategy = self.strategies[provider]

        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Executing tool call: {tool_call.name}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                    },
                )
                result = await strategy.execute_tool(tool_call, max_retries=1, db_session=db_session)

                logger.info(
                    f"Tool call completed: {tool_call.name}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "success": result.success,
                        "execution_time_ms": result.execution_time_ms,
                    },
                )

                if use_cache and cache_key and result.success:
                    await api_response_cache.set(cache_key, result.__dict__, ttl=cache_ttl)

                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Tool execution attempt {attempt + 1} failed: {e}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )

                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue

        logger.error(
            f"Tool execution failed after {max_retries} attempts: {tool_call.name}",
            extra={
                "tool_name": tool_call.name,
                "provider": provider.value,
                "final_error": str(last_exception),
            },
        )

        return ToolResult(
            tool_call_id=tool_call.id,
            success=False,
            content=[],
            error=f"Tool execution failed after {max_retries} attempts: {last_exception}",
            provider=provider,
        )

    async def execute_tool_calls(
        self,
        tool_calls: List[ToolCall],
        max_retries: int = 3,
        use_cache: bool = True,
        parallel_execution: bool = True,
        db_session: Optional[AsyncSession] = None,
    ) -> List[ToolResult]:
        if not tool_calls:
            return []

        logger.info(f"Executing {len(tool_calls)} tool calls")

        if parallel_execution:
            tasks = [
                self.execute_tool_call(tool_call, max_retries=max_retries, use_cache=use_cache, db_session=db_session)
                for tool_call in tool_calls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        ToolResult(
                            tool_call_id=tool_calls[i].id,
                            success=False,
                            content=[],
                            error=str(result),
                        )
                    )
                else:
                    processed_results.append(result)

            return processed_results
        else:
            results = []
            for tool_call in tool_calls:
                result = await self.execute_tool_call(
                    tool_call, max_retries=max_retries, use_cache=use_cache, db_session=db_session
                )
                results.append(result)
            return results

    async def get_available_tools(
        self, provider: Optional[ToolProvider] = None, db_session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        all_tools = []
        strategies_to_check = (
            {provider: self.strategies[provider]}
            if provider and provider in self.strategies
            else self.strategies
        )
        for provider_type, strategy in strategies_to_check.items():
            try:
                tools = await strategy.get_available_tools(db_session)
                for tool in tools:
                    tool["provider"] = provider_type.value
                all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"Failed to get tools from {provider_type}: {e}")
        logger.info(f"Retrieved {len(all_tools)} available tools")
        return all_tools

    async def health_check(self, db_session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        health_status = {
            "unified_tool_executor": {
                "status": "healthy" if self._initialized else "not_initialized",
                "providers": {},
            }
        }
        for provider_type, strategy in self.strategies.items():
            try:
                provider_health = await strategy.health_check(db_session)
                health_status["unified_tool_executor"]["providers"][
                    provider_type.value
                ] = provider_health
            except Exception as e:
                health_status["unified_tool_executor"]["providers"][provider_type.value] = {
                    "status": "error",
                    "error": str(e),
                }
        return health_status

    def _determine_provider(self, tool_name: str) -> ToolProvider:
        if "_" in tool_name and ToolProvider.FASTMCP in self.strategies:
            return ToolProvider.FASTMCP
        if ToolProvider.FASTMCP in self.strategies:
            return ToolProvider.FASTMCP
        raise ExternalServiceError(f"Cannot determine provider for tool: {tool_name}")
