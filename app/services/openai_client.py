"""
OpenAI API client with unified tool integration.

This service provides a wrapper around the OpenAI API with enhanced
functionality including tool calling via UnifiedToolExecutor (now dependency-injected).

"""

import json
from typing import Any, Dict, List, Optional, Union

from ..config import settings
from ..core.logging import get_api_logger
from ..core.tool_executor import ToolCall, UnifiedToolExecutor
from ..schemas.tool_calling import ToolHandlingMode
from ..utils.api_errors import handle_api_errors
from ..utils.caching import embedding_cache, make_cache_key
from ..utils.tool_middleware import RetryConfig, tool_operation

import openai
from openai import AsyncOpenAI

import tiktoken


logger = get_api_logger("openai_client")


class OpenAIClient:
    """
    OpenAI API client with unified tool integration.

    This client provides methods for chat completions, embeddings,
    and content moderation with automatic unified tool calling capabilities.

    Key Features:
    - Unified tool calling through injected UnifiedToolExecutor
    - Consistent error handling via @handle_api_errors decorator
    - Retry logic and caching through middleware decorators
    - Structured logging for all operations
    - Full async/await support for all operations

    Tool Integration:
    - Automatically integrates with UnifiedToolExecutor for tool calling
    - Supports both custom tools and unified tools from multiple providers
    - Handles tool call execution with proper error handling and logging

    Error Handling:
    - Uses @handle_api_errors decorator for consistent error responses
    - Automatic retry logic for rate limits and connection errors
    - Proper exception mapping to HTTP status codes
    """

    def __init__(self, tool_executor: Optional[UnifiedToolExecutor] = None):
        """Initialize OpenAI client with dependency-injected UnifiedToolExecutor."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.tool_executor = tool_executor

        # Initialize tokenizer
        self.tokenizer = None
        try:
            self.tokenizer = tiktoken.encoding_for_model(settings.openai_chat_model)
        except Exception:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.warning(f"Failed to initialize tokenizer: {e}")

    @handle_api_errors("Model validation failed")
    async def validate_model_availability(self) -> bool:
        """
        Validate that the configured models are available.

        Returns:
            bool: True if models are available
        """
        try:
            await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )
            chat_available = True

            try:
                await self.client.embeddings.create(
                    model=settings.openai_embedding_model, input="test"
                )
                embedding_available = True
            except Exception as e:
                logger.warning(
                    f"Embedding model {settings.openai_embedding_model} not available: {e}"
                )
                embedding_available = False

            if not chat_available:
                logger.warning(f"Chat model {settings.openai_chat_model} not available")
            if not embedding_available:
                logger.warning(f"Embedding model {settings.openai_embedding_model} not available")

            return chat_available and embedding_available

        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0

        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Failed to count tokens: {e}")
        return len(text.split()) + len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        total_tokens = 0
        for message in messages:
            total_tokens += 4
            if "role" in message:
                total_tokens += self.count_tokens(message["role"])
            if "content" in message:
                total_tokens += self.count_tokens(message["content"])
            if "name" in message:
                total_tokens += self.count_tokens(message["name"])
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:
                    total_tokens += self.count_tokens(json.dumps(tool_call))
        return total_tokens

    @handle_api_errors("Chat completion failed")
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[Any] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        use_unified_tools: bool = True,
        tool_handling_mode: ToolHandlingMode = ToolHandlingMode.COMPLETE_WITH_RESULTS,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with flexible tool call handling.

        Args:
            messages: List of messages
            llm_profile: LLM profile object containing model parameters (temperature, max_tokens, etc.)
            tools: Custom tools (if None, will use unified tools if available)
            tool_choice: Tool choice strategy
            use_unified_tools: Whether to automatically include unified tools
            tool_handling_mode: How to handle tool call results:
                - RETURN_RESULTS: Return tool results as content without further processing
                - COMPLETE_WITH_RESULTS: Execute tools and feed results back for final completion
            max_retries: Maximum number of retry attempts

        Returns:
            dict: Chat completion response with usage information and tool results
        """
        final_tools = tools or []

        if use_unified_tools and not tools and self.tool_executor:
            try:
                unified_tools = await self.tool_executor.get_available_tools()
                final_tools.extend(unified_tools)
                logger.info(f"Added {len(unified_tools)} unified tools to chat completion")
            except Exception as e:
                logger.warning(f"Failed to add unified tools: {e}")

        request_params = {
            "model": settings.openai_chat_model,
            "messages": messages,
        }

        if llm_profile:
            profile_params = llm_profile.to_openai_params()
            request_params.update(profile_params)
        else:
            request_params["temperature"] = 0.7

        if final_tools:
            request_params["tools"] = final_tools
            request_params["tool_choice"] = tool_choice

        @tool_operation(
            retry_config=RetryConfig(
                max_retries=max_retries,
                retriable_exceptions=(
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                ),
            ),
            enable_caching=False,  # Don't cache chat completions
            log_details=True,
        )
        async def _make_completion():
            response = await self.client.chat.completions.create(**request_params)
            return response

        response = await _make_completion()
        message = response.choices[0].message
        tool_calls_executed = []
        final_content = message.content or ""
        final_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        if message.tool_calls and self.tool_executor:
            tool_calls_executed = await self._execute_unified_tool_calls(message.tool_calls)

            if tool_handling_mode == ToolHandlingMode.RETURN_RESULTS:
                final_content = self._format_tool_results_as_content(tool_calls_executed)
                logger.info("Returning tool results as content without further completion")

            elif tool_handling_mode == ToolHandlingMode.COMPLETE_WITH_RESULTS:
                final_completion = await self._complete_with_tool_results(
                    messages,
                    message.tool_calls,
                    tool_calls_executed,
                    llm_profile,
                )
                final_content = final_completion["content"]
                final_usage["prompt_tokens"] += final_completion["usage"]["prompt_tokens"]
                final_usage["completion_tokens"] += final_completion["usage"]["completion_tokens"]
                final_usage["total_tokens"] += final_completion["usage"]["total_tokens"]
                logger.info("Completed with tool results fed back to OpenAI")

        result = {
            "content": final_content,
            "role": message.role,
            "tool_calls": (
                [tool_call.model_dump() for tool_call in message.tool_calls]
                if message.tool_calls
                else None
            ),
            "tool_calls_executed": tool_calls_executed,
            "finish_reason": response.choices[0].finish_reason,
            "usage": final_usage,
            "tool_handling_mode": tool_handling_mode,
        }

        return result

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        llm_profile: Optional[Any] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        use_unified_tools: bool = True,
        tool_handling_mode: ToolHandlingMode = ToolHandlingMode.COMPLETE_WITH_RESULTS,
        max_retries: int = 3,
    ):
        """
        Create a streaming chat completion with tool call handling.

        Args:
            messages: List of messages
            llm_profile: LLM profile object containing model parameters (temperature, max_tokens, etc.)
            tools: Custom tools (if None, will use unified tools if available)
            tool_choice: Tool choice strategy
            use_unified_tools: Whether to automatically include unified tools
            tool_handling_mode: How to handle tool call results
            max_retries: Maximum number of retry attempts

        Yields:
            dict: Streaming response chunks with content or tool call results
        """
        final_tools = tools or []
        if use_unified_tools and not tools and self.tool_executor:
            try:
                unified_tools = await self.tool_executor.get_available_tools()
                final_tools.extend(unified_tools)
                logger.info(
                    f"Added {len(unified_tools)} unified tools to streaming chat completion"
                )
            except Exception as e:
                logger.warning(f"Failed to add unified tools: {e}")

        request_params = {
            "model": settings.openai_chat_model,
            "messages": messages,
            "stream": True,
        }

        if llm_profile:
            profile_params = llm_profile.to_openai_params()
            request_params.update(profile_params)
        else:
            request_params["temperature"] = 0.7

        if final_tools:
            request_params["tools"] = final_tools
            request_params["tool_choice"] = tool_choice

        try:
            stream = await self.client.chat.completions.create(**request_params)
            tool_calls_data = []
            full_content = ""

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield {"type": "content", "content": content}

                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        if tool_call.function and tool_call.function.name:
                            tool_calls_data.append(tool_call)

            if tool_calls_data and self.tool_executor:
                tool_calls_executed = await self._execute_unified_tool_calls(tool_calls_data)
                for tool_result in tool_calls_executed:
                    yield {
                        "type": "tool_call",
                        "tool": tool_result.get("name"),
                        "result": tool_result.get("result"),
                    }

                if tool_handling_mode == ToolHandlingMode.COMPLETE_WITH_RESULTS:
                    yield {
                        "type": "content",
                        "content": f"\n\n[Tool calls completed: {len(tool_calls_executed)} tools executed]",
                    }

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}")
            yield {"type": "error", "error": str(e)}

    async def _execute_unified_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        try:
            if not self.tool_executor:
                logger.warning("UnifiedToolExecutor not provided")
                return []

            unified_tool_calls = []
            for tool_call in tool_calls:
                unified_tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                    )
                )

            results = await self.tool_executor.execute_tool_calls(unified_tool_calls)
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "tool_call_id": result.tool_call_id,
                        "success": result.success,
                        "content": result.content,
                        "error": result.error,
                        "provider": result.provider.value if result.provider else None,
                        "execution_time_ms": result.execution_time_ms,
                    }
                )
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to execute unified tool calls: {e}")
            return []

    def _format_tool_results_as_content(self, tool_results: List[Dict[str, Any]]) -> str:
        if not tool_results:
            return "No tools were executed."
        content_parts = ["# Tool Execution Results\n"]
        for i, result in enumerate(tool_results, 1):
            content_parts.append(f"## Tool Call {i}: {result.get('tool_call_id', 'Unknown')}\n")

            if result.get("success"):
                content_parts.append("✅ **Status**: Success\n")
                if result.get("content"):
                    content_parts.append("**Result**:")
                    for content_item in result["content"]:
                        if isinstance(content_item, dict):
                            if content_item.get("type") == "text":
                                content_parts.append(f"```\n{content_item.get('text', '')}\n```\n")
                            else:
                                content_parts.append(
                                    f"```json\n{json.dumps(content_item, indent=2)}\n```\n"
                                )
                        else:
                            content_parts.append(f"```\n{str(content_item)}\n```\n")
                else:
                    content_parts.append("*No content returned*\n")
            else:
                content_parts.append("❌ **Status**: Failed\n")
                if result.get("error"):
                    content_parts.append(f"**Error**: {result['error']}\n")

            if result.get("execution_time_ms"):
                content_parts.append(f"**Execution Time**: {result['execution_time_ms']:.2f}ms\n")

            content_parts.append("\n---\n\n")

        return "".join(content_parts)

    async def _complete_with_tool_results(
        self,
        original_messages: List[Dict[str, Any]],
        tool_calls,
        tool_results: List[Dict[str, Any]],
        llm_profile: Optional[Any],
    ) -> Dict[str, Any]:
        completion_messages = original_messages.copy()
        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
        }
        completion_messages.append(assistant_message)
        for tool_call, result in zip(tool_calls, tool_results):
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": self._format_tool_result_for_ai(result),
            }
            completion_messages.append(tool_message)

        @tool_operation(
            retry_config=RetryConfig(
                max_retries=3,
                retriable_exceptions=(
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                ),
            ),
            enable_caching=False,
            log_details=True,
        )
        async def _make_final_completion():
            request_params = {
                "model": settings.openai_chat_model,
                "messages": completion_messages,
            }
            if llm_profile:
                profile_params = llm_profile.to_openai_params()
                request_params.update(profile_params)
            else:
                request_params["temperature"] = 0.7

            response = await self.client.chat.completions.create(**request_params)
            return response

        final_response = await _make_final_completion()
        final_message = final_response.choices[0].message

        return {
            "content": final_message.content or "",
            "role": final_message.role,
            "finish_reason": final_response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": final_response.usage.prompt_tokens,
                "completion_tokens": final_response.usage.completion_tokens,
                "total_tokens": final_response.usage.total_tokens,
            },
        }

    def _format_tool_result_for_ai(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"Tool execution failed: {result.get('error', 'Unknown error')}"

        if not result.get("content"):
            return "Tool executed successfully but returned no content."

        content_parts = []
        for content_item in result["content"]:
            if isinstance(content_item, dict):
                if content_item.get("type") == "text":
                    content_parts.append(content_item.get("text", ""))
                else:
                    content_parts.append(json.dumps(content_item, indent=2))
            else:
                content_parts.append(str(content_item))

        return "\n\n".join(content_parts) if content_parts else "Tool executed successfully."

    @handle_api_errors("Embedding creation failed")
    async def create_embedding(
        self, text: str, encoding_format: Optional[str] = "json", max_retries: int = 3
    ) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        cache_key = make_cache_key("embedding", settings.openai_embedding_model, text.strip())
        cached_embedding = await embedding_cache.get(cache_key)
        if cached_embedding is not None:
            logger.debug("Using cached embedding")
            return cached_embedding

        @tool_operation(
            retry_config=RetryConfig(
                max_retries=max_retries,
                retriable_exceptions=(
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                ),
            ),
            enable_caching=False,
            log_details=True,
        )
        async def _create_embedding():
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text.strip(),
                encoding_format="float",
            )
            return response.data[0].embedding

        embedding = await _create_embedding()
        await embedding_cache.set(cache_key, embedding, ttl=3600)
        return embedding

    @handle_api_errors("Batch embedding creation failed")
    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            return []

        @tool_operation(enable_caching=False, log_details=True)
        async def _create_batch_embeddings():
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model, input=valid_texts
            )
            return [item.embedding for item in response.data]

        return await _create_batch_embeddings()

    @handle_api_errors("Content moderation failed")
    async def moderate_content(self, text: str) -> Dict[str, Any]:
        @tool_operation(cache_ttl=600, log_details=True)
        async def _moderate_content():
            response = await self.client.moderations.create(input=text)
            result = response.results[0]

            return {
                "flagged": result.flagged,
                "categories": result.categories.model_dump(),
                "category_scores": result.category_scores.model_dump(),
            }

        return await _moderate_content()

    @handle_api_errors("OpenAI health check failed", log_errors=False)
    async def health_check(self) -> Dict[str, Any]:
        @tool_operation(enable_caching=False, log_details=False)
        async def _health_check():
            await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )
            embedding_available = True
            try:
                await self.client.embeddings.create(
                    model=settings.openai_embedding_model, input="test"
                )
            except Exception:
                embedding_available = False

            return {
                "openai_available": True,
                "models_available": True,
                "chat_model": settings.openai_chat_model,
                "embedding_model": settings.openai_embedding_model,
                "chat_model_available": True,
                "embedding_model_available": embedding_available,
                "status": "healthy",
            }

        try:
            return await _health_check()
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "openai_available": True,
                "models_available": False,
                "error": str(e),
                "status": "unhealthy",
            }
