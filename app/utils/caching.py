"Utility functions for caching operations."

import asyncio
import hashlib
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    "SimpleCache class for specialized functionality."

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        "Initialize class instance."
        self._cache: Dict[(str, Dict[(str, Any)])] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        "Get operation."
        async with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            item = self._cache[key]
            if time.time() > item["expires_at"]:
                del self._cache[key]
                self.misses += 1
                return None
            self.hits += 1
            return item["value"]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        "Set operation."
        async with self._lock:
            if len(self._cache) >= self.max_size:
                oldest_key = min(
                    self._cache.keys(), key=(lambda k: self._cache[k]["created_at"])
                )
                del self._cache[oldest_key]
            expires_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = {
                "value": value,
                "created_at": time.time(),
                "expires_at": expires_at,
            }

    async def delete(self, key: str) -> bool:
        "Delete operation."
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        "Clear operation."
        async with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    async def cleanup_expired(self) -> int:
        "Cleanup Expired operation."
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for (key, item) in self._cache.items()
                if (current_time > item["expires_at"])
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_stats(self) -> Dict[(str, Any)]:
        "Get stats data."
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if (total_requests > 0) else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


embedding_cache = SimpleCache(default_ttl=3600, max_size=5000)
api_response_cache = SimpleCache(default_ttl=300, max_size=1000)
search_result_cache = SimpleCache(default_ttl=600, max_size=2000)


def make_cache_key(*args, **kwargs) -> str:
    "Make Cache Key operation."
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for (k, v) in sorted(kwargs.items())])
    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()


async def cached_function(cache: SimpleCache, ttl: Optional[int] = None):
    "Cached Function operation."

    def decorator(func):
        "Decorator operation."

        async def wrapper(*args, **kwargs):
            "Wrapper operation."
            cache_key = make_cache_key(func.__name__, *args, **kwargs)
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            result = await func(*args, **kwargs)
            (await cache.set(cache_key, result, ttl))
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result

        return wrapper

    return decorator


async def start_cache_cleanup_task():
    "Start Cache Cleanup Task operation."

    async def cleanup_loop():
        "Cleanup Loop operation."
        while True:
            try:
                (await asyncio.sleep(300))
                for cache_name, cache in [
                    ("embedding", embedding_cache),
                    ("api_response", api_response_cache),
                    ("search_result", search_result_cache),
                ]:
                    removed = await cache.cleanup_expired()
                    if removed > 0:
                        logger.info(
                            f"Cleaned up {removed} expired items from {cache_name} cache"
                        )
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")

    asyncio.create_task(cleanup_loop())
    logger.info("Cache cleanup task started")
