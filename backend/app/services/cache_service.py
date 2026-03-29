"""
Redis caching service for performance optimization.
"""
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings


logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service with intelligent key management and TTL strategies."""

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.default_ttl = settings.REDIS_CACHE_TTL
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool = None

    async def connect(self):
        """Initialize Redis connection with connection pooling."""
        try:
            if not self._connection_pool:
                self._connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=20,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )

            self.redis_client = redis.Redis(connection_pool=self._connection_pool)

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache service connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Redis cache service disconnected")

    async def ensure_connection(self):
        """Ensure Redis connection is active."""
        if not self.redis_client:
            await self.connect()

    def _generate_cache_key(self, key_pattern: str, **kwargs) -> str:
        """Generate a consistent cache key from pattern and parameters."""
        try:
            # Replace placeholders in key pattern
            formatted_key = key_pattern.format(**kwargs)
            return formatted_key
        except KeyError as e:
            logger.error(f"Missing key parameter for cache key generation: {e}")
            raise ValueError(f"Missing parameter {e} for cache key")

    def _generate_hash_key(self, data: Union[str, dict, list]) -> str:
        """Generate MD5 hash for complex data structures."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        else:
            data_str = str(data)

        return hashlib.md5(data_str.encode()).hexdigest()[:16]

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with JSON deserialization."""
        try:
            await self.ensure_connection()

            value = await self.redis_client.get(key)
            if value is None:
                return default

            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with JSON serialization and TTL."""
        try:
            await self.ensure_connection()

            # Serialize value to JSON if it's not a string
            if isinstance(value, (dict, list, bool, int, float)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)

            # Use provided TTL or default
            cache_ttl = ttl if ttl is not None else self.default_ttl

            await self.redis_client.setex(key, cache_ttl, serialized_value)
            logger.debug(f"Cached key {key} with TTL {cache_ttl}")
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.ensure_connection()
            result = await self.redis_client.delete(key)
            logger.debug(f"Deleted cache key {key} (existed: {result > 0})")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            await self.ensure_connection()

            # Find keys matching pattern
            keys = await self.redis_client.keys(pattern)
            if not keys:
                return 0

            # Delete matching keys
            result = await self.redis_client.delete(*keys)
            logger.info(f"Deleted {result} cache keys matching pattern {pattern}")
            return result

        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            await self.ensure_connection()
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists check error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key (-1 if key doesn't exist, -2 if no TTL)."""
        try:
            await self.ensure_connection()
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL check error for key {key}: {e}")
            return -1

    # ========== Specialized Cache Methods ==========

    async def get_product_search_results(self, query: str, filters: dict) -> Optional[List[dict]]:
        """Get cached product search results."""
        query_hash = self._generate_hash_key(query.lower().strip())
        filters_hash = self._generate_hash_key(filters)

        cache_key = self._generate_cache_key(
            "search:{query_hash}:{filters_hash}",
            query_hash=query_hash,
            filters_hash=filters_hash
        )

        return await self.get(cache_key)

    async def cache_product_search_results(
        self,
        query: str,
        filters: dict,
        results: List[dict],
        ttl: int = 3600
    ) -> bool:
        """Cache product search results (TTL: 1 hour by default)."""
        query_hash = self._generate_hash_key(query.lower().strip())
        filters_hash = self._generate_hash_key(filters)

        cache_key = self._generate_cache_key(
            "search:{query_hash}:{filters_hash}",
            query_hash=query_hash,
            filters_hash=filters_hash
        )

        return await self.set(cache_key, results, ttl)

    async def get_user_recommendations(self, user_id: str) -> Optional[List[dict]]:
        """Get cached user recommendations."""
        cache_key = self._generate_cache_key("recommendations:{user_id}", user_id=user_id)
        return await self.get(cache_key)

    async def cache_user_recommendations(
        self,
        user_id: str,
        recommendations: List[dict],
        ttl: int = 14400
    ) -> bool:
        """Cache user recommendations (TTL: 4 hours by default)."""
        cache_key = self._generate_cache_key("recommendations:{user_id}", user_id=user_id)
        return await self.set(cache_key, recommendations, ttl)

    async def get_price_history(self, product_id: str) -> Optional[List[dict]]:
        """Get cached price history for a product."""
        cache_key = self._generate_cache_key("price_history:{product_id}", product_id=product_id)
        return await self.get(cache_key)

    async def cache_price_history(
        self,
        product_id: str,
        price_history: List[dict],
        ttl: int = 1800
    ) -> bool:
        """Cache price history (TTL: 30 minutes by default)."""
        cache_key = self._generate_cache_key("price_history:{product_id}", product_id=product_id)
        return await self.set(cache_key, price_history, ttl)

    async def get_user_analytics(self, user_id: str) -> Optional[dict]:
        """Get cached user analytics summary."""
        cache_key = self._generate_cache_key("analytics:{user_id}", user_id=user_id)
        return await self.get(cache_key)

    async def cache_user_analytics(
        self,
        user_id: str,
        analytics_data: dict,
        ttl: int = 900
    ) -> bool:
        """Cache user analytics (TTL: 15 minutes by default)."""
        cache_key = self._generate_cache_key("analytics:{user_id}", user_id=user_id)
        return await self.set(cache_key, analytics_data, ttl)

    async def get_popular_products(self, category: str) -> Optional[List[dict]]:
        """Get cached popular products for a category."""
        cache_key = self._generate_cache_key("popular:{category}", category=category.lower())
        return await self.get(cache_key)

    async def cache_popular_products(
        self,
        category: str,
        products: List[dict],
        ttl: int = 7200
    ) -> bool:
        """Cache popular products (TTL: 2 hours by default)."""
        cache_key = self._generate_cache_key("popular:{category}", category=category.lower())
        return await self.set(cache_key, products, ttl)

    async def get_dashboard_overview(self, user_id: str) -> Optional[dict]:
        """Get cached dashboard overview data."""
        cache_key = self._generate_cache_key("dashboard:{user_id}", user_id=user_id)
        return await self.get(cache_key)

    async def cache_dashboard_overview(
        self,
        user_id: str,
        dashboard_data: dict,
        ttl: int = 1800
    ) -> bool:
        """Cache dashboard overview (TTL: 30 minutes by default)."""
        cache_key = self._generate_cache_key("dashboard:{user_id}", user_id=user_id)
        return await self.set(cache_key, dashboard_data, ttl)

    # ========== Cache Invalidation Methods ==========

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a specific user."""
        patterns = [
            f"recommendations:{user_id}",
            f"analytics:{user_id}",
            f"dashboard:{user_id}",
            f"user_prefs:{user_id}"
        ]

        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted

        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted

    async def invalidate_product_cache(self, product_id: str) -> int:
        """Invalidate cache entries related to a specific product."""
        patterns = [
            f"price_history:{product_id}",
            f"product:{product_id}",
            "search:*",  # Invalidate all searches as they might include this product
            "popular:*"  # Invalidate popular products as ranking might change
        ]

        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted

        logger.info(f"Invalidated {total_deleted} cache entries for product {product_id}")
        return total_deleted

    async def invalidate_search_cache(self) -> int:
        """Invalidate all product search caches."""
        deleted = await self.delete_pattern("search:*")
        logger.info(f"Invalidated {deleted} search cache entries")
        return deleted

    # ========== Cache Statistics and Health ==========

    async def get_cache_stats(self) -> dict:
        """Get Redis cache statistics."""
        try:
            await self.ensure_connection()

            info = await self.redis_client.info()
            stats = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0)
            }

            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total_requests = hits + misses

            if total_requests > 0:
                stats["hit_rate_percentage"] = round((hits / total_requests) * 100, 2)
            else:
                stats["hit_rate_percentage"] = 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    async def health_check(self) -> dict:
        """Check cache service health."""
        try:
            await self.ensure_connection()

            # Test basic operations
            test_key = f"health_check_{datetime.now().timestamp()}"
            test_value = {"status": "ok", "timestamp": datetime.now().isoformat()}

            # Set and get test
            await self.set(test_key, test_value, 60)
            retrieved = await self.get(test_key)

            # Clean up
            await self.delete(test_key)

            return {
                "status": "healthy",
                "connected": True,
                "read_write_test": retrieved == test_value,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Dependency function to get cache service instance."""
    return cache_service