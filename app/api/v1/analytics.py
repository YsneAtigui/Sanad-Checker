"""Analytics and Statistics API Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.analytics import AnalyticsService
from app.cache import redis_client
from app.config import settings
import json

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    period: str = Query("last_7_days", regex="^(last_7_days|last_30_days|last_90_days)$"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics with trends
    
    **Period options:**
    - last_7_days
    - last_30_days
    - last_90_days
    
    Returns:
    - total_audits: Total audits count
    - total_audits_trend: % change from previous period
    - average_score: Average audit score
    - average_score_trend: % change
    - critical_issues_count: Critical issues found
    - critical_issues_trend: % change
    - ai_agents_accessible: % of accessible AI agents
    - ai_agents_accessible_trend: % change
    """
    
    # Check cache first
    cache_key = f"dashboard_stats:{period}"
    cached = redis_client.get_cached(cache_key)
    
    if cached:
        return cached
    
    # Calculate fresh stats
    analytics = AnalyticsService(db)
    stats = analytics.get_dashboard_stats(period)
    
    # Cache for 5 minutes
    redis_client.set_cached(cache_key, stats, settings.CACHE_TTL_DASHBOARD)
    
    return stats


@router.get("/score-distribution")
async def get_score_distribution(
    db: Session = Depends(get_db)
):
    """
    Get score distribution for all completed audits
    
    Returns:
    - Score ranges with counts:
      - 0-20: count
      - 21-40: count
      - 41-60: count
      - 61-80: count
      - 81-100: count
    """
    
    # Check cache
    cache_key = "score_distribution"
    cached = redis_client.get_cached(cache_key)
    
    if cached:
        return cached
    
    # Calculate fresh distribution
    analytics = AnalyticsService(db)
    distribution = analytics.get_score_distribution()
    
    # Cache for 10 minutes
    redis_client.set_cached(cache_key, distribution, settings.CACHE_TTL_ANALYTICS)
    
    return distribution


@router.get("/platform-breakdown")
async def get_platform_breakdown(
    db: Session = Depends(get_db)
):
    """
    Get breakdown of completed audits by e-commerce platform
    
    Returns:
    - Dictionary with platform names and audit counts:
      - salla: count
      - zid: count
      - shopify: count
      - woocommerce: count
      - unknown: count
    """
    
    # Check cache
    cache_key = "platform_breakdown"
    cached = redis_client.get_cached(cache_key)
    
    if cached:
        return cached
    
    # Calculate fresh breakdown
    analytics = AnalyticsService(db)
    breakdown = analytics.get_platform_breakdown()
    
    # Cache for 10 minutes
    redis_client.set_cached(cache_key, breakdown, settings.CACHE_TTL_ANALYTICS)
    
    return breakdown


@router.get("/audit-trends")
async def get_audit_trends(
    days: int = Query(30, ge=7, le=90, description="Number of days to retrieve (7-90)"),
    db: Session = Depends(get_db)
):
    """
    Get daily audit count trends for the last N days
    
    **Query params:**
    - days: Number of days (7-90, default: 30)
    
    Returns:
    - Array of objects with:
      - date: ISO date string
      - count: Number of completed audits
    """
    
    # Check cache
    cache_key = f"audit_trends:{days}"
    cached = redis_client.get_cached(cache_key)
    
    if cached:
        return cached
    
    # Calculate fresh trends
    analytics = AnalyticsService(db)
    trends = analytics.get_trend_data(days)
    
    # Cache for 10 minutes
    redis_client.set_cached(cache_key, trends, settings.CACHE_TTL_ANALYTICS)
    
    return trends


@router.post("/invalidate-cache")
async def invalidate_analytics_cache():
    """
    Invalidate all analytics caches
    
    **Admin endpoint** - clears all analytics caches to force recalculation
    """
    
    patterns = [
        "dashboard_stats:*",
        "score_distribution",
        "platform_breakdown",
        "audit_trends:*"
    ]
    
    total_invalidated = 0
    for pattern in patterns:
        count = redis_client.invalidate_cache(pattern)
        total_invalidated += count
    
    return {
        "status": "success",
        "caches_invalidated": total_invalidated,
        "message": "All analytics caches cleared"
    }
