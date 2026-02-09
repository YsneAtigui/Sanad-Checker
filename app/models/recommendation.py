"""Audit Recommendation model"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class RecommendationSeverity(str, enum.Enum):
    """Recommendation severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    LOW = "low"


class RecommendationCategory(str, enum.Enum):
    """Recommendation category types"""
    PROTOCOL = "protocol"
    SCHEMA = "schema"
    CONTENT = "content"
    EDGE = "edge"


class AuditRecommendation(Base):
    """Audit recommendation model for actionable improvements"""
    __tablename__ = "audit_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_job_id = Column(UUID(as_uuid=True), ForeignKey("audit_jobs.id", ondelete="CASCADE"), nullable=False)
    
    # Recommendation details
    severity = Column(Enum(RecommendationSeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    code_example = Column(Text)  # Optional code snippet to show
    impact = Column(String, nullable=False)  # Impact description
    
    # Categorization and prioritization
    category = Column(Enum(RecommendationCategory))
    priority = Column(Integer)  # 1-10 for sorting (1 = highest priority)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    audit_job = relationship("AuditJob", back_populates="recommendations")
