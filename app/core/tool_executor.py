"Core tool_executor functionality and business logic."

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
    "ToolProvider class for specialized functionality."

    FASTMCP = "fastmcp"
    OPENAI = "openai"


@dataclass
class ToolCall:
    "ToolCall class for specialized functionality."

    id: str
    name: str
    arguments: Dict[(str, Any)]
    provider: Optional[ToolProvider] = None


@dataclass
class ToolResult:
    "ToolResult class for specialized functionality."

    tool_call_id: str
    success: bool
    content: List[Dict[(str, Any)]]
    error: Optional[str] = None
    provider: Optional[ToolProvider] = None
    execution_time_ms: Optional[float] = None


class ToolExecutionStrategy(ABC):
    "ToolExecutionStrategy class for specialized functionality."

    @abstractmethod
    async def execute_tool(
        self, tool_call: ToolCall, max_retries: int = 3
    ) -> ToolResult:
        "Execute Tool operation."
        pass

    @abstractmethod
    async def get_available_tools(self) -> List[Dict[(str, Any)]]:
        "Get available tools data."
        pass

    @abstractmethod
    async def health_check(self) -> Dict[(str, Any)]:
        "Health Check operation."
        pass


class FastMCPToolStrategy(ToolExecutionStrategy):
    "FastMCPToolStrategy class for specialized functionality."

    def __init__(self, mcp_client):
        "Initialize class instance."
        self.mcp_client = mcp_client

    async def execute_tool(
        self, tool_call: ToolCall, max_retries: int = 3
    ) -> ToolResult:
        "Execute Tool operation."
        import time

        start_time = time.time()
        try:
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

    async def get_available_tools(self) -> List[Dict[(str, Any)]]:
        "Get available tools data."
        if (not self.mcp_client) or (not self.mcp_client.is_initialized):
            return []
        return self.mcp_client.get_tools_for_openai()

    async def health_check(self) -> Dict[(str, Any)]:
        "Health Check operation."
        if not self.mcp_client:
            return {"status": "unavailable", "provider": "fastmcp"}
        return await self.mcp_client.health_check()


class UnifiedToolExecutor:
    "UnifiedToolExecutor class for specialized functionality."

    def __init__(self):
        "Initialize class instance."
        self.strategies: Dict[(ToolProvider, ToolExecutionStrategy)] = {}
        self._initialized = False

    async def initialize(self, mcp_client=None):
        "Initialize operation."
        try:
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
        "Execute Tool Call operation."
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
            raise ExternalServiceError(
                f"No strategy available for provider: {provider}"
            )
        strategy = self.strategies[provider]
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Executing tool call: {tool_call.name}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "attempt": (attempt + 1),
                        "max_retries": max_retries,
                    },
                )
                result = await strategy.execute_tool(tool_call, max_retries=1)
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
                    (
                        await api_response_cache.set(
                            cache_key, result.__dict__, ttl=cache_ttl
                        )
                    )
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Tool execution attempt {(attempt + 1)} failed: {e}",
                    extra={
                        "tool_name": tool_call.name,
                        "provider": provider.value,
                        "attempt": (attempt + 1),
                        "error": str(e),
                    },
                )
                if attempt < (max_retries - 1):
                    wait_time = 2**attempt
                    (await asyncio.sleep(wait_time))
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
    ) -> List[ToolResult]:
        "Execute Tool Calls operation."
        if not tool_calls:
            return []
        logger.info(f"Executing {len(tool_calls)} tool calls")
        if parallel_execution:
            tasks = [
                self.execute_tool_call(
                    tool_call, max_retries=max_retries, use_cache=use_cache
                )
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
                    tool_call, max_retries=max_retries, use_cache=use_cache
                )
                results.append(result)
            return results

    async def get_available_tools(
        self, provider: Optional[ToolProvider] = None
    ) -> List[Dict[(str, Any)]]:
        "Get available tools data."
        all_tools = []
        strategies_to_check = (
            {provider: self.strategies[provider]}
            if (provider and (provider in self.strategies))
            else self.strategies
        )
        for provider_type, strategy in strategies_to_check.items():
            try:
                tools = await strategy.get_available_tools()
                for tool in tools:
                    tool["provider"] = provider_type.value
                all_tools.extend(tools)
            except Exception as e:
                logger.warning(f"Failed to get tools from {provider_type}: {e}")
        logger.info(f"Retrieved {len(all_tools)} available tools")
        return all_tools

    async def health_check(self) -> Dict[(str, Any)]:
        "Health Check operation."
        health_status = {
            "unified_tool_executor": {
                "status": ("healthy" if self._initialized else "not_initialized"),
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
        "Determine Provider operation."
        if ("_" in tool_name) and (ToolProvider.FASTMCP in self.strategies):
            return ToolProvider.FASTMCP
        if ToolProvider.FASTMCP in self.strategies:
            return ToolProvider.FASTMCP
        raise ExternalServiceError(f"Cannot determine provider for tool: {tool_name}")


_unified_tool_executor: Optional[UnifiedToolExecutor] = None


async def get_unified_tool_executor() -> UnifiedToolExecutor:
    "Get unified tool executor data."
    global _unified_tool_executor
    if _unified_tool_executor is None:
        _unified_tool_executor = UnifiedToolExecutor()
        try:
            from ..services.mcp_client import get_mcp_client

            mcp_client = await get_mcp_client()
            (await _unified_tool_executor.initialize(mcp_client=mcp_client))
        except Exception as e:
            logger.warning(f"Failed to initialize with MCP client: {e}")
            (await _unified_tool_executor.initialize())
    return _unified_tool_executor


async def cleanup_unified_tool_executor():
    "Cleanup Unified Tool Executor operation."
    global _unified_tool_executor
    _unified_tool_executor = None
