"""
OpenAI API client with FastMCP tool integration.

This service provides a wrapper around the OpenAI API with enhanced
functionality including tool calling via FastMCP integration.

Generated on: 2025-07-14 04:13:26 UTC
Current User: lllucius
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json

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

from ..config import settings
from ..core.exceptions import ExternalServiceError
from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI API client with FastMCP tool integration.
    
    This client provides methods for chat completions, embeddings,
    and tool calling with automatic MCP integration.
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
                max_tokens=1
            )
            
            # If we get here, the chat model is available
            chat_available = True
            
            # Test embedding model
            try:
                await self.client.embeddings.create(
                    model=settings.openai_embedding_model,
                    input="test"
                )
                embedding_available = True
            except Exception as e:
                logger.warning(f"Embedding model {settings.openai_embedding_model} not available: {e}")
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
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        use_mcp_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Create a chat completion with optional tool calling.
        
        Args:
            messages: List of messages
            temperature: Response randomness (0-2)
            max_tokens: Maximum tokens in response
            tools: Custom tools (if None, will use MCP tools if available)
            tool_choice: Tool choice strategy
            use_mcp_tools: Whether to automatically include MCP tools
            
        Returns:
            dict: Chat completion response with usage information
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")
        
        try:
            # Prepare tools
            final_tools = tools or []
            
            # Add MCP tools if requested and no custom tools provided
            if use_mcp_tools and not tools:
                try:
                    mcp_client = await get_mcp_client()
                    mcp_tools = mcp_client.get_tools_for_openai()
                    final_tools.extend(mcp_tools)
                    logger.info(f"Added {len(mcp_tools)} MCP tools to chat completion")
                except Exception as e:
                    logger.warning(f"Failed to add MCP tools: {e}")
            
            # Prepare request parameters
            request_params = {
                "model": settings.openai_chat_model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            if final_tools:
                request_params["tools"] = final_tools
                request_params["tool_choice"] = tool_choice
            
            # Make the API call
            response = await self.client.chat.completions.create(**request_params)
            
            message = response.choices[0].message
            
            # Handle tool calls
            tool_calls_made = []
            if message.tool_calls:
                tool_calls_made = await self._execute_tool_calls(message.tool_calls)
                
                # Add tool call results to conversation if needed
                # This would require continuing the conversation with tool results
            
            # Format response
            result = {
                "content": message.content or "",
                "role": message.role,
                "tool_calls": [tool_call.model_dump() for tool_call in message.tool_calls] if message.tool_calls else None,
                "tool_calls_executed": tool_calls_made,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise ExternalServiceError(f"Chat completion failed: {e}")
    
    async def _execute_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute tool calls using FastMCP."""
        try:
            mcp_client = await get_mcp_client()
            
            # Convert OpenAI tool calls to MCP format
            mcp_tool_calls = []
            for tool_call in tool_calls:
                mcp_tool_calls.append({
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            # Execute tool calls
            results = await mcp_client.execute_tool_calls(mcp_tool_calls)
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute tool calls: {e}")
            return []
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        if not OPENAI_AVAILABLE or not self.client:
            raise ExternalServiceError("OpenAI client not available")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text.strip()
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise ExternalServiceError(f"Embedding creation failed: {e}")
    
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
        
        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=valid_texts
            )
            
            return [item.embedding for item in response.data]
            
        except Exception as e:
            logger.error(f"Batch embedding creation failed: {e}")
            raise ExternalServiceError(f"Batch embedding creation failed: {e}")
    
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
        
        try:
            response = await self.client.moderations.create(input=text)
            result = response.results[0]
            
            return {
                "flagged": result.flagged,
                "categories": result.categories.model_dump(),
                "category_scores": result.category_scores.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Content moderation failed: {e}")
            raise ExternalServiceError(f"Content moderation failed: {e}")
    
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
                "error": "OpenAI client not available"
            }
        
        try:
            # Test with a simple completion
            test_response = await self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            
            # Test embedding
            try:
                await self.client.embeddings.create(
                    model=settings.openai_embedding_model,
                    input="test"
                )
                embedding_available = True
            except Exception:
                embedding_available = False
            
            return {
                "openai_available": True,
                "models_available": True,
                "chat_model": settings.openai_chat_model,
                "embedding_model": settings.openai_embedding_model,
                "chat_model_available": True,
                "embedding_model_available": embedding_available,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "openai_available": True,
                "models_available": False,
                "error": str(e),
                "status": "unhealthy"
            }