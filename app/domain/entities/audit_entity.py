"""Domain entities for Sanad AEO Auditor.

Pure business objects without framework dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from enum import Enum


class AuditStatus(str, Enum):
    """Audit job status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AuditScore:
    """Value object for audit scoring with validation."""
    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Score must be between 0-100, got {self.value}")

    def is_passing(self, threshold: int = 70) -> bool:
        """Check if score passes a threshold."""
        return self.value >= threshold

    def grade(self) -> str:
        """Get letter grade for score."""
        if self.value >= 90:
            return "A"
        elif self.value >= 80:
            return "B"
        elif self.value >= 70:
            return "C"
        elif self.value >= 60:
            return "D"
        else:
            return "F"


@dataclass
class AuditIssueEntity:
    """Domain entity for audit issues."""
    id: UUID
    audit_job_id: UUID
    issue_type: str
    severity: IssueSeverity
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    affected_field: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None


@dataclass
class AuditEntity:
    """Core audit domain entity with business logic."""
    
    id: UUID
    url: str
    status: AuditStatus
    created_at: datetime
    
    # Optional fields
    platform: Optional[str] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Results
    protocol_results: Optional[Dict] = None
    schema_results: Optional[Dict] = None
    content_results: Optional[Dict] = None
    edge_results: Optional[Dict] = None
    bilingual_results: Optional[Dict] = None
    
    # Scoring
    overall_score: Optional[int] = None
    severity_counts: Optional[Dict[str, int]] = None
    
    # Storage paths
    raw_html_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    report_markdown: Optional[str] = None
    
    # Related entities
    issues: List[AuditIssueEntity] = field(default_factory=list)
    
    def is_completed(self) -> bool:
        """Check if audit is completed successfully."""
        return self.status == AuditStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if audit has failed."""
        return self.status == AuditStatus.FAILED
    
    def is_processing(self) -> bool:
        """Check if audit is currently processing."""
        return self.status in (AuditStatus.QUEUED, AuditStatus.IN_PROGRESS)
    
    def mark_in_progress(self) -> None:
        """Mark audit as in progress."""
        if self.status != AuditStatus.QUEUED:
            raise ValueError(f"Can only start queued audits. Current status: {self.status}")
        self.status = AuditStatus.IN_PROGRESS
    
    def mark_completed(self, overall_score: int) -> None:
        """Mark audit as completed with score."""
        if self.status != AuditStatus.IN_PROGRESS:
            raise ValueError(f"Can only complete in-progress audits. Current status: {self.status}")
        
        self.status = AuditStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.overall_score = overall_score
        self.error_message = None
    
    def mark_failed(self, error_message: str) -> None:
        """Mark audit as failed with error message."""
        self.status = AuditStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def get_score_object(self) -> Optional[AuditScore]:
        """Get validated score object."""
        if self.overall_score is None:
            return None
        return AuditScore(value=self.overall_score)
    
    def count_issues_by_severity(self) -> Dict[str, int]:
        """Count issues grouped by severity."""
        counts = {severity.value: 0 for severity in IssueSeverity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts
    
    def has_critical_issues(self) -> bool:
        """Check if audit has any critical issues."""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)
