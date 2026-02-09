"""Analytics service for dashboard statistics and metrics"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import AuditJob, AuditStatus


class AnalyticsService:
    """Service for calculating analytics and statistics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, period: str = "last_7_days") -> Dict:
        """
        Get dashboard statistics for the specified period
        
        Args:
            period: Time period (last_7_days, last_30_days, last_90_days)
            
        Returns:
            Dictionary with stats and trends
        """
        # Determine date ranges
        current_start, current_end = self._get_period_dates(period)
        previous_start, previous_end = self._get_previous_period_dates(period)
        
        # Current period stats
        current_stats = self._calculate_period_stats(current_start, current_end)
        
        # Previous period stats for trend calculation
        previous_stats = self._calculate_period_stats(previous_start, previous_end)
        
        # Calculate trends
        return {
            "total_audits": current_stats["total_audits"],
            "total_audits_trend": self._calculate_trend(
                current_stats["total_audits"],
                previous_stats["total_audits"]
            ),
            "average_score": current_stats["average_score"],
            "average_score_trend": self._calculate_trend(
                current_stats["average_score"],
                previous_stats["average_score"]
            ),
            "critical_issues_count": current_stats["critical_issues"],
            "critical_issues_trend": self._calculate_trend(
                current_stats["critical_issues"],
                previous_stats["critical_issues"]
            ),
            "ai_agents_accessible": current_stats["ai_agents_accessible"],
            "ai_agents_accessible_trend": self._calculate_trend(
                current_stats["ai_agents_accessible"],
                previous_stats["ai_agents_accessible"]
            ),
            "period": period
        }
    
    def get_score_distribution(self) -> Dict:
        """
        Get score distribution for completed audits
        
        Returns:
            Dictionary with score ranges and counts
        """
        audits = self.db.query(AuditJob).filter(
            AuditJob.status == AuditStatus.COMPLETED,
            AuditJob.overall_score.isnot(None)
        ).all()
        
        distribution = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }
        
        for audit in audits:
            score = audit.overall_score
            if score <= 20:
                distribution["0-20"] += 1
            elif score <= 40:
                distribution["21-40"] += 1
            elif score <= 60:
                distribution["41-60"] += 1
            elif score <= 80:
                distribution["61-80"] += 1
            else:
                distribution["81-100"] += 1
        
        return distribution
    
    def get_platform_breakdown(self) -> Dict:
        """
        Get breakdown of audits by platform
        
        Returns:
            Dictionary with platform counts
        """
        results = self.db.query(
            AuditJob.platform,
            func.count(AuditJob.id).label('count')
        ).filter(
            AuditJob.status == AuditStatus.COMPLETED
        ).group_by(AuditJob.platform).all()
        
        return {
            platform or "Unknown": count 
            for platform, count in results
        }
    
    def get_trend_data(self, days: int = 30) -> List[Dict]:
        """
        Get daily audit counts for the last N days
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of dictionaries with date and count
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query audits grouped by date
        results = self.db.query(
            func.date(AuditJob.created_at).label('date'),
            func.count(AuditJob.id).label('count')
        ).filter(
            AuditJob.created_at >= start_date,
            AuditJob.status == AuditStatus.COMPLETED
        ).group_by(
            func.date(AuditJob.created_at)
        ).order_by('date').all()
        
        return [
            {
                "date": str(date),
                "count": count
            }
            for date, count in results
        ]
    
    def _get_period_dates(self, period: str) -> tuple:
        """Get start and end dates for the current period"""
        end_date = datetime.utcnow()
        
        if period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif period == "last_90_days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        return start_date, end_date
    
    def _get_previous_period_dates(self, period: str) -> tuple:
        """Get start and end dates for the previous period (for trend comparison)"""
        current_start, current_end = self._get_period_dates(period)
        period_length = (current_end - current_start).days
        
        previous_end = current_start
        previous_start = previous_end - timedelta(days=period_length)
        
        return previous_start, previous_end
    
    def _calculate_period_stats(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate statistics for a given period"""
        # Query audits in this period
        audits = self.db.query(AuditJob).filter(
            and_(
                AuditJob.created_at >= start_date,
                AuditJob.created_at < end_date,
                AuditJob.status == AuditStatus.COMPLETED
            )
        ).all()
        
        if not audits:
            return {
                "total_audits": 0,
                "average_score": 0.0,
                "critical_issues": 0,
                "ai_agents_accessible": 0.0
            }
        
        # Calculate metrics
        total_audits = len(audits)
        total_score = sum(audit.overall_score or 0 for audit in audits)
        average_score = round(total_score / total_audits, 1) if total_audits > 0 else 0.0
        
        # Count critical issues
        critical_issues = sum(
            (audit.severity_counts or {}).get("critical", 0)
            for audit in audits
        )
        
        # Calculate AI agent accessibility percentage
        accessible_count = 0
        total_agents_tested = 0
        
        for audit in audits:
            if audit.edge_results and isinstance(audit.edge_results, dict):
                agents = audit.edge_results.get("agents", [])
                for agent in agents:
                    total_agents_tested += 1
                    if agent.get("status") == "accessible":
                        accessible_count += 1
        
        ai_agents_accessible = round(
            (accessible_count / total_agents_tested * 100) if total_agents_tested > 0 else 0.0,
            1
        )
        
        return {
            "total_audits": total_audits,
            "average_score": average_score,
            "critical_issues": critical_issues,
            "ai_agents_accessible": ai_agents_accessible
        }
    
    def _calculate_trend(self, current: float, previous: float) -> str:
        """
        Calculate trend percentage change
        
        Args:
            current: Current period value
            previous: Previous period value
            
        Returns:
            Trend string with + or - prefix (e.g., "+12.5", "-5.3", "0")
        """
        if previous == 0:
            if current > 0:
                return "+100.0"
            return "0"
        
        change = ((current - previous) / previous) * 100
        
        if change > 0:
            return f"+{change:.1f}"
        elif change < 0:
            return f"{change:.1f}"
        else:
            return "0"
