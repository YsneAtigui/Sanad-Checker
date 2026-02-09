import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class AuditStatus(str, enum.Enum):
    """Audit job status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, enum.Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditJob(Base):
    """Audit job model"""
    __tablename__ = "audit_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, nullable=False)
    platform = Column(String)  # salla, zid, shopify, unknown
    status = Column(Enum(AuditStatus), default=AuditStatus.QUEUED)
    
    # Results (JSON columns)
    # Each JSON field follows a standardized schema documented below
    
    #protocol_results schema: {"checks": [...], "score": int}
    # - checks: list of {"name": str, "status": str, "detail": str, "raw_content": str}
    # - score: 0-100
    protocol_results = Column(JSON)
    
    # schema_results schema: {"fields": [...], "extracted_jsonld": str, "schema_type": str, "score": int}
    # - fields: list of {"field": str, "status": str, "visible_value": str, "structured_value": str}
    # - score: 0-100
    schema_results = Column(JSON)
    
    # content_results schema: {"aeo_readiness_score": int, "robotic_pattern_score": str, "issues": [...], "score": int}
    # - issues: list of {"type": str, "severity": str, "description": str, "location": str}
    # - score: 0-100
    content_results = Column(JSON)
    
    # edge_results schema: {"agents": [...], "cloudflare_detected": bool, "bot_challenge_enabled": bool, "score": int}
    # - agents: list of {"name": str, "icon": str, "status": str, "response_time_ms": int, "data_completeness": str}
    # - score: 0-100
    edge_results = Column(JSON)
    
    # bilingual_results schema: {"has_arabic": bool, "has_english": bool, "consistency_score": int, "issues": [...]}
    bilingual_results = Column(JSON)
    
    # Scoring
    overall_score = Column(Integer)  # 0-100
    severity_counts = Column(JSON)  # {critical: 2, high: 3, ...}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Storage
    raw_html_path = Column(String)
    screenshot_path = Column(String)
    report_markdown = Column(Text)
    
    # Relationships
    issues = relationship("AuditIssue", back_populates="audit_job", cascade="all, delete-orphan")
    recommendations = relationship("AuditRecommendation", back_populates="audit_job", cascade="all, delete-orphan")



class AuditIssue(Base):
    """Audit issue model"""
    __tablename__ = "audit_issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_job_id = Column(UUID(as_uuid=True), ForeignKey("audit_jobs.id", ondelete="CASCADE"))
    
    issue_type = Column(String, nullable=False)
    severity = Column(Enum(IssueSeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    recommendation = Column(Text)
    
    # Context
    affected_field = Column(String)
    expected_value = Column(String)
    actual_value = Column(String)
    
    # Relationship
    audit_job = relationship("AuditJob", back_populates="issues")
