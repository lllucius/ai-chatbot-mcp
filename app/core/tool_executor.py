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

from ..core.exceptions import ExternalServiceError
from ..utils.api_errors import handle_api_errors
from ..utils.caching import api_response_cache, make_cache_key
from ..utils.logging import get_api_logger

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
    async def execute_tool(
        self, tool_call: ToolCall, max_retries: int = 3
    ) -> ToolResult:
        """Execute a single tool call."""
        pass

    @abstractmethod
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check health of the tool provider."""
        pass


class FastMCPToolStrategy(ToolExecutionStrategy):
    """Tool execution strategy for FastMCP tools."""

    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    async def execute_tool(
        self, tool_call: ToolCall, max_retries: int = 3
    ) -> ToolResult:
        """Execute a FastMCP tool call with retry logic."""
        import time

        start_time = time.time()

        try:
            # Call the MCP tool
            result = await self.mcp_client.call_tool(
                tool_call.name, tool_call.arguments
            )

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_call_id=tool_call.id,
                success=result.get("success", True),
                content=result.get("content", []),
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

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available FastMCP tools."""
        if not self.mcp_client or not self.mcp_client.is_initialized:
            return []
        return self.mcp_client.get_tools_for_openai()

    async def health_check(self) -> Dict[str, Any]:
        """Check FastMCP health."""
        if not self.mcp_client:
            return {"status": "unavailable", "provider": "fastmcp"}
        return await self.mcp_client.health_check()


class UnifiedToolExecutor:
    """
    Unified tool executor that centralizes all tool calling logic.

    This class provides a single interface for executing tools from different
    providers (FastMCP, OpenAI) with consistent retry, caching, and error
    handling behavior.
    """

    def __init__(self):
        """Initialize the unified tool executor."""
        self.strategies: Dict[ToolProvider, ToolExecutionStrategy] = {}
        self._initialized = False

    async def initialize(self, mcp_client=None):
        """
        Initialize tool execution strategies.

        Args:
            mcp_client: FastMCP client instance for MCP tool execution
        """
        try:
            # Initialize FastMCP strategy if client provided
            if mcp_client:
                self.strategies[ToolProvider.FASTMCP] = FastMCPToolStrategy(mcp_client)
                logger.info("FastMCP tool strategy initialized")

            self._initialized = True
            logger.info(
                f"UnifiedToolExecutor initialized with {len(self.strategies)} strategies"
            )

        except Exception as e:
            logger.error(f"Failed to initialize UnifiedToolExecutor: {e}")
            raise ExternalServiceError(f"Tool executor initialization failed: {e}")

    @handle_api_errors("Tool execution failed")
    async def execute_tool_call(
        self,
        tool_call: ToolCall,
        max_retries: int = 3,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> ToolResult:
        """
        Execute a single tool call with retry logic and caching.

        Args:
            tool_call: Tool call to execute
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use caching for results
            cache_ttl: Cache time-to-live in seconds

        Returns:
            ToolResult: Result of tool execution
        """
        if not self._initialized:
            raise ExternalServiceError("Tool executor not initialized")

        # Create cache key if caching is enabled
        cache_key = None
        if use_cache:
            cache_key = make_cache_key("tool_call", tool_call.name, tool_call.arguments)

            # Check cache first
            cached_result = await api_response_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for tool call: {tool_call.name}")
                return ToolResult(**cached_result)

        # Determine provider and strategy
        provider = tool_call.provider or self._determine_provider(tool_call.name)
        if provider not in self.strategies:
            raise ExternalServiceError(
                f"No strategy available for provider: {provider}"
            )

        strategy = self.strategies[provider]

        # Execute with retry logic
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

                result = await strategy.execute_tool(tool_call, max_retries=1)

                # Log result
                logger.info(
                    f"Tool call completed: {tool_call.name}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "success": result.success,
                        "execution_time_ms": result.execution_time_ms,
                    },
                )

                # Cache successful results
                if use_cache and cache_key and result.success:
                    await api_response_cache.set(
                        cache_key, result.__dict__, ttl=cache_ttl
                    )

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

        # All retries failed
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
    ) -> List[ToolResult]:
        """
        Execute multiple tool calls with optional parallel execution.

        Args:
            tool_calls: List of tool calls to execute
            max_retries: Maximum retry attempts per tool call
            use_cache: Whether to use caching
            parallel_execution: Whether to execute tools in parallel

        Returns:
            List[ToolResult]: Results of all tool executions
        """
        if not tool_calls:
            return []

        logger.info(f"Executing {len(tool_calls)} tool calls")

        if parallel_execution:
            # Execute tools in parallel
            tasks = [
                self.execute_tool_call(
                    tool_call, max_retries=max_retries, use_cache=use_cache
                )
                for tool_call in tool_calls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error results
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
            # Execute tools sequentially
            results = []
            for tool_call in tool_calls:
                result = await self.execute_tool_call(
                    tool_call, max_retries=max_retries, use_cache=use_cache
                )
                results.append(result)
            return results

    async def get_available_tools(
        self, provider: Optional[ToolProvider] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available tools from all or specific providers.

        Args:
            provider: Specific provider to get tools from, or None for all

        Returns:
            List of available tools
        """
        all_tools = []

        strategies_to_check = (
            {provider: self.strategies[provider]}
            if provider and provider in self.strategies
            else self.strategies
        )

        for provider_type, strategy in strategies_to_check.items():
            try:
                tools = await strategy.get_available_tools()
                # Add provider information to each tool
                for tool in tools:
                    tool["provider"] = provider_type.value
                all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"Failed to get tools from {provider_type}: {e}")

        logger.info(f"Retrieved {len(all_tools)} available tools")
        return all_tools

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all tool providers.

        Returns:
            Dict containing health status of all providers
        """
        health_status = {
            "unified_tool_executor": {
                "status": "healthy" if self._initialized else "not_initialized",
                "providers": {},
            }
        }

        for provider_type, strategy in self.strategies.items():
            try:
                provider_health = await strategy.health_check()
                health_status["unified_tool_executor"]["providers"][
                    provider_type.value
                ] = provider_health
            except Exception as e:
                health_status["unified_tool_executor"]["providers"][
                    provider_type.value
                ] = {"status": "error", "error": str(e)}

        return health_status

    def _determine_provider(self, tool_name: str) -> ToolProvider:
        """
        Determine the provider for a tool based on tool name patterns.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolProvider for the tool
        """
        # FastMCP tools are typically prefixed with server name
        if "_" in tool_name and ToolProvider.FASTMCP in self.strategies:
            return ToolProvider.FASTMCP

        # Default to FastMCP if available
        if ToolProvider.FASTMCP in self.strategies:
            return ToolProvider.FASTMCP

        # If no suitable provider found, raise error
        raise ExternalServiceError(f"Cannot determine provider for tool: {tool_name}")


# Global instance
_unified_tool_executor: Optional[UnifiedToolExecutor] = None


async def get_unified_tool_executor() -> UnifiedToolExecutor:
    """Get or create the global unified tool executor instance."""
    global _unified_tool_executor

    if _unified_tool_executor is None:
        _unified_tool_executor = UnifiedToolExecutor()

        # Initialize with available MCP client
        try:
            from ..services.mcp_client import get_mcp_client

            mcp_client = await get_mcp_client()
            await _unified_tool_executor.initialize(mcp_client=mcp_client)
        except Exception as e:
            logger.warning(f"Failed to initialize with MCP client: {e}")
            await _unified_tool_executor.initialize()

    return _unified_tool_executor


async def cleanup_unified_tool_executor():
    """Cleanup the global unified tool executor instance."""
    global _unified_tool_executor
    _unified_tool_executor = None
