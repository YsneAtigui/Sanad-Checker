from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


class AuditRequest(BaseModel):
    """Request to create an audit"""
    url: HttpUrl
    include_bilingual: bool = True
    deep_content_analysis: bool = True


class AuditResponse(BaseModel):
    """Response after creating audit"""
    audit_id: UUID
    status: str
    estimated_time_seconds: int = 45


class IssueResponse(BaseModel):
    """Single audit issue"""
    id: UUID
    issue_type: str
    severity: str
    title: str
    description: Optional[str]
    recommendation: Optional[str]
    
    class Config:
        from_attributes = True


class AuditStatusResponse(BaseModel):
    """Audit status and results"""
    audit_id: UUID
    url: str
    status: str
    platform: Optional[str]
    overall_score: Optional[int]
    severity_counts: Optional[Dict[str, int]]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    issues: List[IssueResponse] = []
    
    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """List of audits"""
    audits: List[AuditStatusResponse]
    total: int
    limit: int
    offset: int
