"Utility functions for rate_limiting operations."

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from ..config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    "RateLimiter class for specialized functionality."

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        "Initialize class instance."
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[(str, list)] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> tuple[(bool, Optional[int])]:
        "Check if allowed condition is met."
        async with self._lock:
            current_time = time.time()
            client_requests = self.requests[client_id]
            client_requests[:] = [
                req_time
                for req_time in client_requests
                if ((current_time - req_time) < self.time_window)
            ]
            if len(client_requests) >= self.max_requests:
                oldest_request = (
                    min(client_requests) if client_requests else current_time
                )
                retry_after = (
                    int((self.time_window - (current_time - oldest_request))) + 1
                )
                return (False, retry_after)
            client_requests.append(current_time)
            return (True, None)

    async def cleanup_old_entries(self):
        "Cleanup Old Entries operation."
        async with self._lock:
            current_time = time.time()
            clients_to_remove = []
            for client_id, requests in self.requests.items():
                requests[:] = [
                    req_time
                    for req_time in requests
                    if ((current_time - req_time) < self.time_window)
                ]
                if not requests:
                    clients_to_remove.append(client_id)
            for client_id in clients_to_remove:
                del self.requests[client_id]


general_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests, time_window=settings.rate_limit_period
)
auth_limiter = RateLimiter(max_requests=10, time_window=300)
upload_limiter = RateLimiter(max_requests=20, time_window=3600)


async def rate_limit_middleware(request: Request, call_next):
    "Rate Limit Middleware operation."
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    client_id = f"{client_ip}:{(hash(user_agent) % 10000)}"
    path = request.url.path
    if "/auth/" in path:
        limiter = auth_limiter
    elif "/upload" in path:
        limiter = upload_limiter
    else:
        limiter = general_limiter
    (is_allowed, retry_after) = await limiter.is_allowed(client_id)
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for client {client_id} on path {path}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=({"Retry-After": str(retry_after)} if retry_after else {}),
        )
    response = await call_next(request)
    return response


async def start_rate_limiter_cleanup():
    "Start Rate Limiter Cleanup operation."

    async def cleanup_loop():
        "Cleanup Loop operation."
        while True:
            try:
                (await asyncio.sleep(300))
                (await general_limiter.cleanup_old_entries())
                (await auth_limiter.cleanup_old_entries())
                (await upload_limiter.cleanup_old_entries())
                logger.debug("Rate limiter cleanup completed")
            except Exception as e:
                logger.error(f"Rate limiter cleanup failed: {e}")

    asyncio.create_task(cleanup_loop())
    logger.info("Rate limiter cleanup task started")


def get_rate_limiter_stats() -> Dict[(str, int)]:
    "Get rate limiter stats data."
    return {
        "general_clients": len(general_limiter.requests),
        "auth_clients": len(auth_limiter.requests),
        "upload_clients": len(upload_limiter.requests),
    }
