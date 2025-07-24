"""
Centralized retry and caching utilities for tool operations.

This module provides decorators and utilities for consistent retry logic,
caching behavior, and error handling across tool operations.

"""

import asyncio
import functools
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple, Type

from ..utils.caching import api_response_cache, make_cache_key
from ..core.logging import get_component_logger

logger = get_component_logger("tool_middleware")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retriable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


def with_retry(config: Optional[RetryConfig] = None, log_attempts: bool = True):
    """
    Decorator to add retry logic to tool operations.

    Args:
        config: Retry configuration, uses defaults if None
        log_attempts: Whether to log retry attempts

    Returns:
        Decorator function that adds retry logic

    Example:
        @with_retry(RetryConfig(max_retries=5))
        async def call_external_api():
            # API call implementation
            pass
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_retries):
                try:
                    if log_attempts and attempt > 0:
                        logger.info(
                            f"Retrying {func.__name__} (attempt {attempt + 1}/{config.max_retries})",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": config.max_retries,
                            },
                        )

                    result = await func(*args, **kwargs)

                    if attempt > 0 and log_attempts:
                        logger.info(
                            f"Successfully completed {func.__name__} after {attempt + 1} attempts",
                            extra={"function": func.__name__, "attempts": attempt + 1},
                        )

                    return result

                except config.retriable_exceptions as e:
                    last_exception = e

                    if log_attempts:
                        logger.warning(
                            f"Attempt {attempt + 1} of {func.__name__} failed: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )

                    # Don't sleep on the last attempt
                    if attempt < config.max_retries - 1:
                        delay = min(
                            config.base_delay * (config.exponential_base**attempt),
                            config.max_delay,
                        )

                        # Add jitter to prevent thundering herd
                        if config.jitter:
                            import random

                            delay *= 0.5 + random.random() * 0.5

                        await asyncio.sleep(delay)
                        continue

            # All retries failed
            if log_attempts:
                logger.error(
                    f"All {config.max_retries} attempts of {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "max_retries": config.max_retries,
                        "final_error": str(last_exception),
                    },
                )

            raise last_exception

        return wrapper

    return decorator


def with_tool_caching(
    cache_key_builder: Optional[Callable] = None,
    ttl: int = 300,
    cache_failures: bool = False,
    failure_ttl: int = 60,
):
    """
    Decorator to add caching to tool operations.

    Args:
        cache_key_builder: Function to build cache key from args/kwargs
        ttl: Time-to-live for successful results in seconds
        cache_failures: Whether to cache failed results
        failure_ttl: TTL for failed results in seconds

    Returns:
        Decorator function that adds caching

    Example:
        @with_tool_caching(ttl=600)
        async def expensive_tool_operation(param1, param2):
            # Expensive operation implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if cache_key_builder:
                cache_key = cache_key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = await api_response_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(
                    f"Cache hit for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "cache_key": (
                            cache_key[:50] + "..." if len(cache_key) > 50 else cache_key
                        ),
                    },
                )

                # Handle cached failures
                if isinstance(cached_result, dict) and cached_result.get(
                    "_cached_failure"
                ):
                    raise Exception(cached_result["error"])

                return cached_result

            # Cache miss - execute function
            try:
                result = await func(*args, **kwargs)

                # Cache successful result
                await api_response_cache.set(cache_key, result, ttl=ttl)

                logger.debug(
                    f"Cache miss for {func.__name__}, result cached",
                    extra={
                        "function": func.__name__,
                        "cache_key": (
                            cache_key[:50] + "..." if len(cache_key) > 50 else cache_key
                        ),
                    },
                )

                return result

            except Exception as e:
                # Optionally cache failures to prevent repeated expensive failures
                if cache_failures:
                    cached_failure = {
                        "_cached_failure": True,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                    await api_response_cache.set(
                        cache_key, cached_failure, ttl=failure_ttl
                    )

                    logger.debug(
                        f"Cached failure for {func.__name__}",
                        extra={"function": func.__name__, "error": str(e)},
                    )

                raise e

        return wrapper

    return decorator


def with_structured_logging(
    log_entry: bool = True,
    log_exit: bool = True,
    log_args: bool = False,
    log_result: bool = False,
    sensitive_params: Optional[List[str]] = None,
):
    """
    Decorator to add structured logging to tool operations.

    Args:
        log_entry: Whether to log function entry
        log_exit: Whether to log function exit
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        sensitive_params: List of parameter names to redact

    Returns:
        Decorator function that adds structured logging
    """
    if sensitive_params is None:
        sensitive_params = ["password", "token", "key", "secret"]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import time

            start_time = time.time()

            # Build log context
            log_context = {"function": func.__name__, "start_time": start_time}

            # Add args if requested (with redaction)
            if log_args:
                # Redact sensitive parameters
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if any(sensitive in k.lower() for sensitive in sensitive_params):
                        safe_kwargs[k] = "[REDACTED]"
                    else:
                        safe_kwargs[k] = v

                log_context.update({"args_count": len(args), "kwargs": safe_kwargs})

            # Log entry
            if log_entry:
                logger.info(f"Entering {func.__name__}", extra=log_context)

            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                # Update log context with success info
                log_context.update(
                    {"success": True, "execution_time_ms": execution_time}
                )

                # Add result if requested (with size limits)
                if log_result:
                    result_str = str(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    log_context["result_preview"] = result_str

                # Log exit
                if log_exit:
                    logger.info(
                        f"Exiting {func.__name__} successfully", extra=log_context
                    )

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                # Update log context with failure info
                log_context.update(
                    {
                        "success": False,
                        "execution_time_ms": execution_time,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

                # Log error exit
                if log_exit:
                    logger.error(
                        f"Exiting {func.__name__} with error", extra=log_context
                    )

                raise

        return wrapper

    return decorator


# Commonly used decorator combinations
def tool_operation(
    retry_config: Optional[RetryConfig] = None,
    cache_ttl: int = 300,
    enable_caching: bool = True,
    log_details: bool = True,
):
    """
    Combined decorator for tool operations with retry, caching, and logging.

    Args:
        retry_config: Retry configuration
        cache_ttl: Cache TTL in seconds
        enable_caching: Whether to enable caching
        log_details: Whether to enable detailed logging

    Returns:
        Combined decorator function

    Example:
        @tool_operation(cache_ttl=600)
        async def my_tool_function():
            # Implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        # Apply decorators in reverse order (inside-out)
        decorated_func = func

        # Apply structured logging first (innermost)
        if log_details:
            decorated_func = with_structured_logging(
                log_entry=True,
                log_exit=True,
                log_args=False,  # Don't log args by default for security
                log_result=False,  # Don't log results by default for performance
            )(decorated_func)

        # Apply caching
        if enable_caching:
            decorated_func = with_tool_caching(ttl=cache_ttl)(decorated_func)

        # Apply retry logic (outermost)
        decorated_func = with_retry(retry_config)(decorated_func)

        return decorated_func

    return decorator
