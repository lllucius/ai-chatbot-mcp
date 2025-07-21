"""
OpenAI API client with unified tool integration.

This service provides a wrapper around the OpenAI API with enhanced
functionality including tool calling via unified tool executor.

Generated on: 2025-07-14 04:13:26 UTC
Updated on: 2025-01-20 20:40:00 UTC
Current User: lllucius / assistant
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from ..config import settings
from ..core.exceptions import ExternalServiceError
from ..core.tool_executor import get_unified_tool_executor, ToolCall
from ..utils.caching import embedding_cache, make_cache_key
from ..utils.api_errors import handle_api_errors
from ..utils.tool_middleware import tool_operation, RetryConfig
from ..utils.logging import get_api_logger

try:
    import openai
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available. Install with: pip install openai")

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("Tiktoken not available. Install with: pip install tiktoken")


logger = get_api_logger("openai_client")


class OpenAIClient:
    """
    OpenAI API client with unified tool integration.

    This client provides methods for chat completions, embeddings,
    and content moderation with automatic unified tool calling capabilities.
    
    Key Features:
    - Unified tool calling through UnifiedToolExecutor
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

    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - AI features disabled")
            self.client = None
            return

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        # Initialize tokenizer
        self.tokenizer = None
        if TIKTOKEN_AVAILABLE:
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
        if not OPENAI_AVAILABLE or not self.client:
            return False

        try:
            # Test with a simple completion to validate model availability
            test_response = await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )

            # If we get here, the chat model is available
            chat_available = True

            # Test embedding model
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
                logger.warning(
                    f"Embedding model {settings.openai_embedding_model} not available"
                )

            return chat_available and embedding_available

        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            int: Number of tokens
        """
        if not text:
            return 0

        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Failed to count tokens: {e}")

        # Fallback: approximate token count
        return len(text.split()) + len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count tokens in a list of messages.

        Args:
            messages: List of message dictionaries

        Returns:
            int: Total number of tokens
        """
        total_tokens = 0

        for message in messages:
            # Count tokens for role and content
            total_tokens += 4  # Base tokens per message

            if "role" in message:
                total_tokens += self.count_tokens(message["role"])

            if "content" in message:
                total_tokens += self.count_tokens(message["content"])

            if "name" in message:
                total_tokens += self.count_tokens(message["name"])

            # Tool calls add extra tokens
            if "tool_calls" in message and message["tool_calls"]:
                for tool_call in message["tool_calls"]:
                    total_tokens += self.count_tokens(json.dumps(tool_call))

        return total_tokens

    @handle_api_errors("Chat completion failed")
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        use_unified_tools: bool = True,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Create a chat completion with unified tool calling and retry logic.

        Args:
            messages: List of messages
            temperature: Response randomness (0-2)
            max_tokens: Maximum tokens in response
            tools: Custom tools (if None, will use unified tools if available)
            tool_choice: Tool choice strategy
            use_unified_tools: Whether to automatically include unified tools
            max_retries: Maximum number of retry attempts

        Returns:
            dict: Chat completion response with usage information
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")

        # Prepare tools using unified tool executor
        final_tools = tools or []

        if use_unified_tools and not tools:
            try:
                tool_executor = await get_unified_tool_executor()
                unified_tools = await tool_executor.get_available_tools()
                final_tools.extend(unified_tools)
                logger.info(f"Added {len(unified_tools)} unified tools to chat completion")
            except Exception as e:
                logger.warning(f"Failed to add unified tools: {e}")

        # Prepare request parameters
        request_params = {
            "model": settings.openai_chat_model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            request_params["max_tokens"] = max_tokens

        if final_tools:
            request_params["tools"] = final_tools
            request_params["tool_choice"] = tool_choice

        # Use retry logic from middleware
        @tool_operation(
            retry_config=RetryConfig(
                max_retries=max_retries,
                retriable_exceptions=(
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                )
            ),
            enable_caching=False,  # Don't cache chat completions
            log_details=True
        )
        async def _make_completion():
            response = await self.client.chat.completions.create(**request_params)
            return response

        response = await _make_completion()
        message = response.choices[0].message

        # Handle tool calls using unified executor
        tool_calls_executed = []
        if message.tool_calls:
            tool_calls_executed = await self._execute_unified_tool_calls(message.tool_calls)

        # Format response
        result = {
            "content": message.content or "",
            "role": message.role,
            "tool_calls": [
                tool_call.model_dump() for tool_call in message.tool_calls
            ]
            if message.tool_calls
            else None,
            "tool_calls_executed": tool_calls_executed,
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

        return result

    async def _execute_unified_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute tool calls using unified tool executor."""
        try:
            tool_executor = await get_unified_tool_executor()

            # Convert OpenAI tool calls to unified format
            unified_tool_calls = []
            for tool_call in tool_calls:
                unified_tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                    )
                )

            # Execute tool calls using unified executor
            results = await tool_executor.execute_tool_calls(unified_tool_calls)
            
            # Convert results to expected format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "tool_call_id": result.tool_call_id,
                    "success": result.success,
                    "content": result.content,
                    "error": result.error,
                    "provider": result.provider.value if result.provider else None,
                    "execution_time_ms": result.execution_time_ms,
                })
            
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to execute unified tool calls: {e}")
            return []

    @handle_api_errors("Embedding creation failed")
    async def create_embedding(
        self, text: str, encoding_format: Optional[str] = "json", max_retries: int = 3
    ) -> List[float]:
        """
        Create embedding for text with caching and retry logic.

        Args:
            text: Text to embed
            encoding_format: Output encoding format
            max_retries: Maximum number of retry attempts

        Returns:
            List[float]: Embedding vector
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Check cache first
        cache_key = make_cache_key("embedding", settings.openai_embedding_model, text.strip())
        cached_embedding = await embedding_cache.get(cache_key)
        if cached_embedding is not None:
            logger.debug("Using cached embedding")
            return cached_embedding

        # Use retry logic from middleware
        @tool_operation(
            retry_config=RetryConfig(
                max_retries=max_retries,
                retriable_exceptions=(
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                )
            ),
            enable_caching=False,  # Manual caching above
            log_details=True
        )
        async def _create_embedding():
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text.strip(),
                encoding_format="float",
            )
            return response.data[0].embedding

        embedding = await _create_embedding()
        
        # Cache the result
        await embedding_cache.set(cache_key, embedding, ttl=3600)  # Cache for 1 hour
        
        return embedding

    @handle_api_errors("Batch embedding creation failed")
    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")

        if not texts:
            return []

        # Filter out empty texts
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
        """
        Moderate content using OpenAI's moderation API.

        Args:
            text: Text to moderate

        Returns:
            dict: Moderation results
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")

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
        """
        Check OpenAI API health.

        Returns:
            dict: Health status
        """
        if not OPENAI_AVAILABLE or not self.client:
            return {
                "openai_available": False,
                "models_available": False,
                "error": "OpenAI client not available",
            }

        @tool_operation(enable_caching=False, log_details=False)
        async def _health_check():
            # Test with a simple completion
            await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )

            # Test embedding
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
