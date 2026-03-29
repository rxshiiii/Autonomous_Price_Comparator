"""
Rate limiter using Redis and token bucket algorithm.
Prevents exceeding platform-specific rate limits.
"""
import asyncio
import time
from typing import Optional
import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger()


class RateLimiter:
    """
    Token bucket rate limiter using Redis.

    Allows burst traffic up to the bucket capacity while
    maintaining an average rate over time.
    """

    def __init__(
        self,
        platform: str,
        rate_limit: int,  # requests per minute
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize rate limiter.

        Args:
            platform: Platform name (used as Redis key prefix)
            rate_limit: Maximum requests per minute
            redis_client: Optional Redis client (creates new if not provided)
        """
        self.platform = platform
        self.rate_limit = rate_limit
        self.redis_client = redis_client
        self.redis_key = f"rate_limit:{platform}"

        # Token bucket parameters
        self.capacity = rate_limit  # Max tokens in bucket
        self.refill_rate = rate_limit / 60.0  # Tokens added per second

        self.logger = logger.bind(platform=platform, rate_limit=rate_limit)

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.

        This method blocks until tokens are available.

        Args:
            tokens: Number of tokens to acquire (default 1)

        Returns:
            True when tokens are acquired
        """
        client = await self._get_redis_client()

        while True:
            # Get current bucket state
            bucket_data = await client.hgetall(self.redis_key)

            current_time = time.time()

            if bucket_data:
                # Existing bucket
                last_refill = float(bucket_data.get("last_refill", current_time))
                available_tokens = float(bucket_data.get("tokens", self.capacity))
            else:
                # New bucket
                last_refill = current_time
                available_tokens = self.capacity

            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            available_tokens = min(self.capacity, available_tokens + tokens_to_add)

            if available_tokens >= tokens:
                # Tokens available - consume them
                new_tokens = available_tokens - tokens

                # Update Redis
                await client.hset(
                    self.redis_key,
                    mapping={
                        "tokens": str(new_tokens),
                        "last_refill": str(current_time)
                    }
                )

                # Set expiry (cleanup after inactivity)
                await client.expire(self.redis_key, 3600)  # 1 hour

                self.logger.debug(
                    "tokens_acquired",
                    tokens=tokens,
                    remaining=new_tokens,
                    capacity=self.capacity
                )

                return True

            else:
                # Not enough tokens - calculate wait time
                tokens_needed = tokens - available_tokens
                wait_time = tokens_needed / self.refill_rate

                self.logger.info(
                    "rate_limited",
                    tokens_needed=tokens_needed,
                    wait_time=wait_time,
                    available=available_tokens
                )

                # Wait for tokens to refill
                await asyncio.sleep(wait_time)

    async def check_available(self) -> float:
        """
        Check how many tokens are currently available.

        Returns:
            Number of available tokens
        """
        client = await self._get_redis_client()
        bucket_data = await client.hgetall(self.redis_key)

        if not bucket_data:
            return self.capacity

        current_time = time.time()
        last_refill = float(bucket_data.get("last_refill", current_time))
        available_tokens = float(bucket_data.get("tokens", self.capacity))

        # Calculate tokens added since last refill
        time_elapsed = current_time - last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        available_tokens = min(self.capacity, available_tokens + tokens_to_add)

        return available_tokens

    async def reset(self):
        """Reset the rate limiter (clear all tokens)."""
        client = await self._get_redis_client()
        await client.delete(self.redis_key)
        self.logger.info("rate_limiter_reset")

    async def get_status(self) -> dict:
        """
        Get current rate limiter status.

        Returns:
            Dictionary with rate limiter status
        """
        available = await self.check_available()

        return {
            "platform": self.platform,
            "rate_limit": self.rate_limit,
            "capacity": self.capacity,
            "available_tokens": available,
            "utilization": (self.capacity - available) / self.capacity,
            "refill_rate": self.refill_rate,
        }

    async def close(self):
        """Close Redis client."""
        if self.redis_client:
            await self.redis_client.aclose()
