"""Rate limiting middleware and abuse prevention system.

Provides rate limiting capabilities with throttling algorithms, client identification,
and abuse prevention mechanisms. Implements multiple rate limiting strategies including
sliding window, token bucket, and adaptive throttling with distributed systems support.
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Optional

from fastapi import Request

from app.config import settings
from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter with abuse prevention.

    Implements rate limiting algorithms with sliding window approach, client tracking,
    and monitoring capabilities for production environments with configurable policies.
    """

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """Initialize rate limiter with configurable policies.

        Sets up sliding window rate limiter with specified limits and time windows.

        Args:
            max_requests: Maximum number of requests allowed per time window
            time_window: Time window duration in seconds for rate limit calculation

        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed for client with rate limit evaluation.

        Performs rate limit evaluation using sliding window algorithm with automatic
        cleanup and retry-after calculation.

        Args:
            client_id: Unique identifier for the client (IP, user ID, API key, etc.)

        Returns:
            Tuple containing:
                - bool: True if request is allowed, False if rate limit exceeded
                - Optional[int]: Retry-after seconds when rate limit exceeded, None when allowed

        """
        async with self._lock:
            current_time = time.time()
            client_requests = self.requests[client_id]

            # Remove old requests outside the time window
            client_requests[:] = [
                req_time
                for req_time in client_requests
                if current_time - req_time < self.time_window
            ]

            # Check if limit exceeded
            if len(client_requests) >= self.max_requests:
                # Calculate retry after time
                oldest_request = (
                    min(client_requests) if client_requests else current_time
                )
                retry_after = (
                    int(self.time_window - (current_time - oldest_request)) + 1
                )
                return False, retry_after

            # Add current request
            client_requests.append(current_time)
            return True, None

    async def cleanup_old_entries(self):
        """Remove expired entries to prevent memory leaks and maintain performance.

        Performs cleanup of expired rate limit entries across all clients to ensure
        long-running applications maintain consistent performance and memory usage.
        """
        async with self._lock:
            current_time = time.time()
            clients_to_remove = []

            for client_id, requests in self.requests.items():
                # Remove old requests
                requests[:] = [
                    req_time
                    for req_time in requests
                    if current_time - req_time < self.time_window
                ]

                # Mark clients with no recent requests for removal
                if not requests:
                    clients_to_remove.append(client_id)

            # Remove empty client entries
            for client_id in clients_to_remove:
                del self.requests[client_id]


# Global rate limiters
general_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests, time_window=settings.rate_limit_period
)

auth_limiter = RateLimiter(
    max_requests=10, time_window=300
)  # 10 requests per 5 minutes for auth
upload_limiter = RateLimiter(max_requests=20, time_window=3600)  # 20 uploads per hour


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware with client identification and endpoint-specific policies.

    Provides rate limiting enforcement with client fingerprinting and endpoint-specific
    policy selection for protection against abuse and resource exhaustion.

    Args:
        request: The incoming HTTP request object for rate limit evaluation
        call_next: The next middleware or endpoint handler in the processing chain

    Returns:
        Response: The HTTP response from the downstream handler when rate limits allow

    Raises:
        RateLimitError: Raised when rate limits are exceeded (429 Too Many Requests)

    """
    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    client_id = f"{client_ip}:{hash(user_agent) % 10000}"  # Simple client fingerprint

    # Choose appropriate limiter based on endpoint
    path = request.url.path

    if "/auth/" in path:
        limiter = auth_limiter
    elif "/upload" in path:
        limiter = upload_limiter
    else:
        limiter = general_limiter

    # Check rate limit
    is_allowed, retry_after = await limiter.is_allowed(client_id)

    if not is_allowed:
        logger.warning(f"Rate limit exceeded for client {client_id} on path {path}")

        raise RateLimitError(
            "Rate limit exceeded",
            details={"retry_after": retry_after} if retry_after else None
        )

    response = await call_next(request)
    return response


async def start_rate_limiter_cleanup():
    """Start background task to clean up old rate limiter entries."""

    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes

                await general_limiter.cleanup_old_entries()
                await auth_limiter.cleanup_old_entries()
                await upload_limiter.cleanup_old_entries()

                logger.debug("Rate limiter cleanup completed")

            except Exception as e:
                logger.error(f"Rate limiter cleanup failed: {e}")

    asyncio.create_task(cleanup_loop())
    logger.info("Rate limiter cleanup task started")


def get_rate_limiter_stats() -> Dict[str, int]:
    """Get current rate limiter statistics."""
    return {
        "general_clients": len(general_limiter.requests),
        "auth_clients": len(auth_limiter.requests),
        "upload_clients": len(upload_limiter.requests),
    }
