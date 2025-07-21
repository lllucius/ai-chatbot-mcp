"""
Rate limiting middleware and utilities for API security.

This module provides rate limiting functionality to protect against
abuse, DDoS attacks, and excessive API usage.

Generated on: 2025-07-14 05:30:00 UTC
Current User: lllucius
"""

import asyncio
import logging
import time
from typing import Dict, Optional
from collections import defaultdict

from fastapi import HTTPException, Request, status
from ..config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter with sliding window approach.

    For production use, consider Redis-based rate limiting for
    distributed systems.
    """

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed for the given client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            tuple: (is_allowed, retry_after_seconds)
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
        """Remove old entries to prevent memory leak."""
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
    """
    Rate limiting middleware for all requests.
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

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)} if retry_after else {},
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
