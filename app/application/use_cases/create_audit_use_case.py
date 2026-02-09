"""Use case for creating a new audit."""

from uuid import uuid4
from datetime import datetime

from app.domain.entities import AuditEntity, AuditStatus
from app.domain.repositories import IAuditRepository
from app.application.dto import CreateAuditDTO, AuditDTO
from app.domain.value_objects import AuditURL


class CreateAuditUseCase:
    """Business logic for creating a new audit.
    
    This use case:
    1. Validates the input URL
    2. Creates an audit entity in queued status
    3. Persists it via repository
    4. Returns the audit ID for task queuing
    """
    
    def __init__(self, repository: IAuditRepository):
        """Initialize use case with repository dependency.
        
        Args:
            repository: Audit repository implementation
        """
        self.repository = repository
    
    def execute(self, dto: CreateAuditDTO) -> AuditDTO:
        """Execute the create audit use case.
        
        Args:
            dto: Create audit input data
            
        Returns:
            AuditDTO with created audit details
            
        Raises:
            ValueError: If URL is invalid
        """
        # Validate URL using value object
        audit_url = AuditURL(value=dto.url)
        
        # Create domain entity
        audit_entity = AuditEntity(
            id=uuid4(),
            url=audit_url.value,
            status=AuditStatus.QUEUED,
            created_at=datetime.utcnow(),
        )
        
        # Persist via repository
        created_audit = self.repository.create(audit_entity)
        
        # Return DTO
        return AuditDTO(
            audit_id=created_audit.id,
            url=created_audit.url,
            status=created_audit.status.value,
            platform=created_audit.platform,
            overall_score=created_audit.overall_score,
            severity_counts=created_audit.severity_counts,
            created_at=created_audit.created_at,
            completed_at=created_audit.completed_at,
            error_message=created_audit.error_message,
        )
