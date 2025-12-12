import logging
import time

import redis.asyncio as redis

from app.redis_db.client import redis_client

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    def __init__(self, redis_client: redis.Redis, max_requests: int = 3, window_seconds: int = 60) -> None:
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    @staticmethod
    def _get_key(ip: str) -> str:
        return f"rate_limit:{ip}"

    async def is_allowed(self, ip: str) -> bool:
        """
        Check if request from IP is allowed based on rate limit.

        Algorithm: Sliding Window with Sorted Sets
        1. Get current timestamp
        2. Calculate window start time (current - window_seconds)
        3. Remove expired requests older than window start
        4. Count remaining requests in the window
        5. If under limit, add current request timestamp
        """
        key = self._get_key(ip)
        current_time = time.time()
        window_start = current_time - self.window

        try:
            pipe = self.redis.pipeline()
            # remove old requests
            await pipe.zremrangebyscore(key, 0, window_start)
            # count requests
            await pipe.zcard(key)
            results = await pipe.execute()
            removed_count = results[0]
            current_count = results[1]

            if current_count < self.max_requests:
                await self.redis.zadd(key, {f"{current_time:.6f}": current_time})
                # prevent memory leaks for old requests
                await self.redis.expire(key, self.window + 10)
                return True
            return False

        except Exception as e:
            logger.error(f"Error checking rate limit for {ip}: {e}", exc_info=True)
            return False


rate_limiter = RedisRateLimiter(
    redis_client=redis_client,
    max_requests=3,
    window_seconds=60,
)
