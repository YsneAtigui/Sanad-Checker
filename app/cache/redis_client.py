"""Redis cache client and utilities"""
import json
from typing import Any, Optional
from redis import Redis
from app.config import settings


class RedisClient:
    """Redis client wrapper with utility methods"""
    
    def __init__(self):
        # Parse Redis URL to get connection params
        redis_url = settings.REDIS_URL
        self.client = Redis.from_url(redis_url, decode_responses=True)
    
    def get_cached(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (deserialized from JSON) or None
        """
        value = self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def set_cached(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            serialized = json.dumps(value)
            return self.client.setex(key, ttl, serialized)
        except (TypeError, ValueError):
            # If value can't be JSON serialized, store as string
            return self.client.setex(key, ttl, str(value))
    
    def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cache keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "audit:*")
            
        Returns:
            Number of keys deleted
        """
        keys = self.client.keys(pattern)
        if keys:
            return self.client.delete(*keys)
        return 0
    
    def invalidate_audit_cache(self, audit_id: str) -> None:
        """
        Invalidate all cache keys related to an audit
        
        Args:
            audit_id: Audit ID
        """
        patterns = [
            f"audit:{audit_id}:*",
            f"audit_detail:{audit_id}",
            "analytics:*",  # Invalidate analytics since audit data changed
            "audits:list:*"  # Invalidate list caches
        ]
        for pattern in patterns:
            self.invalidate_cache(pattern)
    
    def health_check(self) -> bool:
        """
        Check if Redis is accessible
        
        Returns:
            True if Redis is healthy
        """
        try:
            return self.client.ping()
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()


# Cache key generators
def audit_detail_key(audit_id: str) -> str:
    """Generate cache key for audit detail"""
    return f"audit_detail:{audit_id}"


def dashboard_stats_key(period: str) -> str:
    """Generate cache key for dashboard stats"""
    return f"analytics:dashboard:{period}"


def audits_list_key(filters: dict) -> str:
    """Generate cache key for audits list with filters"""
    filter_str = "_".join(f"{k}={v}" for k, v in sorted(filters.items()) if v)
    return f"audits:list:{filter_str}" if filter_str else "audits:list:all"
