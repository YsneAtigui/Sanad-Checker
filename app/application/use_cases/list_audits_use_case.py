"""Use case for listing audits with filtering and pagination."""

from typing import Optional

from app.domain.entities import AuditStatus
from app.domain.repositories import IAuditRepository
from app.application.dto import (
    ListAuditsDTO,
    AuditListResultDTO,
    AuditDTO,
)


class ListAuditsUseCase:
    """Business logic for listing audits with filters."""
    
    def __init__(self, repository: IAuditRepository):
        """Initialize use case with repository dependency.
        
        Args:
            repository: Audit repository implementation
        """
        self.repository = repository
    
    def execute(self, dto: ListAuditsDTO) -> AuditListResultDTO:
        """Execute the list audits use case.
        
        Args:
            dto: List audits input with filters and pagination
            
        Returns:
            AuditListResultDTO with audits and total count
        """
        # Convert status string to enum if provided
        status_enum = None
        if dto.status:
            try:
                status_enum = AuditStatus(dto.status)
            except ValueError:
                raise ValueError(f"Invalid status: {dto.status}")
        
        # Retrieve from repository
        audits, total = self.repository.list_audits(
            limit=dto.pagination.limit,
            offset=dto.pagination.offset,
            status=status_enum,
            platform=dto.platform,
        )
        
        # Convert to DTOs
        audit_dtos = [
            AuditDTO(
                audit_id=audit.id,
                url=audit.url,
                status=audit.status.value,
                platform=audit.platform,
                overall_score=audit.overall_score,
                severity_counts=audit.severity_counts,
                created_at=audit.created_at,
                completed_at=audit.completed_at,
                error_message=audit.error_message,
            )
            for audit in audits
        ]
        
        return AuditListResultDTO(
            audits=audit_dtos,
            total=total,
            limit=dto.pagination.limit,
            offset=dto.pagination.offset,
        )
