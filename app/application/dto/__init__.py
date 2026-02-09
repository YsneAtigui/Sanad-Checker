"""Data Transfer Objects for application layer."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID
from pydantic import HttpUrl


@dataclass
class CreateAuditDTO:
    """DTO for creating a new audit."""
    url: str
    include_bilingual: bool = True
    deep_content_analysis: bool = True


@dataclass
class AuditDTO:
    """DTO for audit output."""
    audit_id: UUID
    url: str
    status: str
    platform: Optional[str] = None
    overall_score: Optional[int] = None
    severity_counts: Optional[Dict[str, int]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class AuditDetailDTO:
    """DTO for detailed audit output with issues."""
    audit_id: UUID
    url: str
    status: str
    platform: Optional[str] = None
    overall_score: Optional[int] = None
    severity_counts: Optional[Dict[str, int]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    protocol_results: Optional[Dict] = None
    schema_results: Optional[Dict] = None
    content_results: Optional[Dict] = None
    edge_results: Optional[Dict] = None
    bilingual_results: Optional[Dict] = None
    issues: List[Dict] = None


@dataclass
class PaginationDTO:
    """DTO for pagination parameters."""
    limit: int = 20
    offset: int = 0
    
    def __post_init__(self):
        """Validate pagination parameters."""
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


@dataclass
class ListAuditsDTO:
    """DTO for listing audits with filters."""
    pagination: PaginationDTO
    status: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class AuditListResultDTO:
    """DTO for audit list results."""
    audits: List[AuditDTO]
    total: int
    limit: int
    offset: int
