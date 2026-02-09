"""SQLAlchemy implementation of audit repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities import AuditEntity, AuditStatus
from app.domain.repositories import IAuditRepository
from app.models.audit import AuditJob, AuditStatus as ModelAuditStatus
from app.infrastructure.persistence.mappers import (
    audit_model_to_entity,
    audit_entity_to_model,
)


class SQLAlchemyAuditRepository(IAuditRepository):
    """Concrete implementation of audit repository using SQLAlchemy."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def create(self, audit: AuditEntity) -> AuditEntity:
        """Create a new audit in database.
        
        Args:
            audit: Audit entity to persist
            
        Returns:
            Created audit entity with ID
        """
        model = audit_entity_to_model(audit)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        return audit_model_to_entity(model)
    
    def get_by_id(self, audit_id: UUID) -> Optional[AuditEntity]:
        """Retrieve audit by ID from database.
        
        Args:
            audit_id: UUID of the audit
            
        Returns:
            Audit entity if found, None otherwise
        """
        model = self.db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        
        if not model:
            return None
        
        return audit_model_to_entity(model)
    
    def update(self, audit: AuditEntity) -> AuditEntity:
        """Update an existing audit in database.
        
        Args:
            audit: Audit entity with updated values
            
        Returns:
            Updated audit entity
            
        Raises:
            ValueError: If audit not found
        """
        existing_model = self.db.query(AuditJob).filter(AuditJob.id == audit.id).first()
        
        if not existing_model:
            raise ValueError(f"Audit with ID {audit.id} not found")
        
        # Update the model
        model = audit_entity_to_model(audit, existing_model)
        self.db.commit()
        self.db.refresh(model)
        
        return audit_model_to_entity(model)
    
    def delete(self, audit_id: UUID) -> bool:
        """Delete an audit from database.
        
        Args:
            audit_id: UUID of the audit to delete
            
        Returns:
            True if deleted, False if not found
        """
        model = self.db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        
        if not model:
            return False
        
        self.db.delete(model)
        self.db.commit()
        
        return True
    
    def list_audits(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[AuditStatus] = None,
        platform: Optional[str] = None
    ) -> tuple[List[AuditEntity], int]:
        """List audits with optional filtering.
        
        Args:
            limit: Maximum number of results
            offset: Pagination offset
            status: Optional status filter
            platform: Optional platform filter
            
        Returns:
            Tuple of (list of audit entities, total count)
        """
        # Build query
        query = self.db.query(AuditJob)
        
        # Apply filters
        if status:
            query = query.filter(AuditJob.status == ModelAuditStatus(status.value))
        
        if platform:
            query = query.filter(AuditJob.platform == platform)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and order
        models = (
            query
            .order_by(AuditJob.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        # Convert to entities
        entities = [audit_model_to_entity(model) for model in models]
        
        return entities, total
