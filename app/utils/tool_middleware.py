"Utility functions for tool_middleware operations."

import asyncio
import functools
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple, Type
from ..utils.caching import api_response_cache, make_cache_key
from ..utils.logging import get_api_logger

logger = get_api_logger("tool_middleware")


@dataclass
class RetryConfig:
    "RetryConfig class for specialized functionality."

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retriable_exceptions: Tuple[(Type[Exception], ...)] = (Exception,)


def with_retry(config: Optional[RetryConfig] = None, log_attempts: bool = True):
    "With Retry operation."
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        "Decorator operation."

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            "Wrapper operation."
            last_exception = None
            for attempt in range(config.max_retries):
                try:
                    if log_attempts and (attempt > 0):
                        logger.info(
                            f"Retrying {func.__name__} (attempt {(attempt + 1)}/{config.max_retries})",
                            extra={
                                "function": func.__name__,
                                "attempt": (attempt + 1),
                                "max_retries": config.max_retries,
                            },
                        )
                    result = await func(*args, **kwargs)
                    if (attempt > 0) and log_attempts:
                        logger.info(
                            f"Successfully completed {func.__name__} after {(attempt + 1)} attempts",
                            extra={
                                "function": func.__name__,
                                "attempts": (attempt + 1),
                            },
                        )
                    return result
                except config.retriable_exceptions as e:
                    last_exception = e
                    if log_attempts:
                        logger.warning(
                            f"Attempt {(attempt + 1)} of {func.__name__} failed: {e}",
                            extra={
                                "function": func.__name__,
                                "attempt": (attempt + 1),
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                    if attempt < (config.max_retries - 1):
                        delay = min(
                            (config.base_delay * (config.exponential_base**attempt)),
                            config.max_delay,
                        )
                        if config.jitter:
                            import random

                            delay *= 0.5 + (random.random() * 0.5)
                        (await asyncio.sleep(delay))
                        continue
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
    "With Tool Caching operation."

    def decorator(func: Callable) -> Callable:
        "Decorator operation."

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            "Wrapper operation."
            if cache_key_builder:
                cache_key = cache_key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(func.__name__, *args, **kwargs)
            cached_result = await api_response_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(
                    f"Cache hit for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "cache_key": (
                            (cache_key[:50] + "...")
                            if (len(cache_key) > 50)
                            else cache_key
                        ),
                    },
                )
                if isinstance(cached_result, dict) and cached_result.get(
                    "_cached_failure"
                ):
                    raise Exception(cached_result["error"])
                return cached_result
            try:
                result = await func(*args, **kwargs)
                (await api_response_cache.set(cache_key, result, ttl=ttl))
                logger.debug(
                    f"Cache miss for {func.__name__}, result cached",
                    extra={
                        "function": func.__name__,
                        "cache_key": (
                            (cache_key[:50] + "...")
                            if (len(cache_key) > 50)
                            else cache_key
                        ),
                    },
                )
                return result
            except Exception as e:
                if cache_failures:
                    cached_failure = {
                        "_cached_failure": True,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                    (
                        await api_response_cache.set(
                            cache_key, cached_failure, ttl=failure_ttl
                        )
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
    "With Structured Logging operation."
    if sensitive_params is None:
        sensitive_params = ["password", "token", "key", "secret"]

    def decorator(func: Callable) -> Callable:
        "Decorator operation."

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            "Wrapper operation."
            import time

            start_time = time.time()
            log_context = {"function": func.__name__, "start_time": start_time}
            if log_args:
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if any(
                        ((sensitive in k.lower()) for sensitive in sensitive_params)
                    ):
                        safe_kwargs[k] = "[REDACTED]"
                    else:
                        safe_kwargs[k] = v
                log_context.update({"args_count": len(args), "kwargs": safe_kwargs})
            if log_entry:
                logger.info(f"Entering {func.__name__}", extra=log_context)
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                log_context.update(
                    {"success": True, "execution_time_ms": execution_time}
                )
                if log_result:
                    result_str = str(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    log_context["result_preview"] = result_str
                if log_exit:
                    logger.info(
                        f"Exiting {func.__name__} successfully", extra=log_context
                    )
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                log_context.update(
                    {
                        "success": False,
                        "execution_time_ms": execution_time,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                if log_exit:
                    logger.error(
                        f"Exiting {func.__name__} with error", extra=log_context
                    )
                raise

        return wrapper

    return decorator


def tool_operation(
    retry_config: Optional[RetryConfig] = None,
    cache_ttl: int = 300,
    enable_caching: bool = True,
    log_details: bool = True,
):
    "Tool Operation operation."

    def decorator(func: Callable) -> Callable:
        "Decorator operation."
        decorated_func = func
        if log_details:
            decorated_func = with_structured_logging(
                log_entry=True, log_exit=True, log_args=False, log_result=False
            )(decorated_func)
        if enable_caching:
            decorated_func = with_tool_caching(ttl=cache_ttl)(decorated_func)
        decorated_func = with_retry(retry_config)(decorated_func)
        return decorated_func

    return decorator
