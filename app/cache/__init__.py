"""Cache package initialization"""
from app.cache.redis_client import redis_client, audit_detail_key, dashboard_stats_key, audits_list_key

__all__ = [
    "redis_client",
    "audit_detail_key",
    "dashboard_stats_key",
    "audits_list_key"
]
