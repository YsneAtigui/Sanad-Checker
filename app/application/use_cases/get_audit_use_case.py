"""Use case for retrieving audit details."""

from uuid import UUID
from typing import Optional

from app.domain.repositories import IAuditRepository
from app.application.dto import AuditDetailDTO


class GetAuditUseCase:
    """Business logic for retrieving an audit by ID."""
    
    def __init__(self, repository: IAuditRepository):
        """Initialize use case with repository dependency.
        
        Args:
            repository: Audit repository implementation
        """
        self.repository = repository
    
    def execute(self, audit_id: UUID) -> Optional[AuditDetailDTO]:
        """Execute the get audit use case.
        
        Args:
            audit_id: UUID of the audit to retrieve
            
        Returns:
            AuditDetailDTO if found, None otherwise
        """
        # Retrieve from repository
        audit_entity = self.repository.get_by_id(audit_id)
        
        if not audit_entity:
            return None
        
        # Convert issues to dict format
        issues = [
            {
                "id": str(issue.id),
                "issue_type": issue.issue_type,
                "severity": issue.severity.value,
                "title": issue.title,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "affected_field": issue.affected_field,
                "expected_value": issue.expected_value,
                "actual_value": issue.actual_value,
            }
            for issue in audit_entity.issues
        ]
        
        # Return detailed DTO
        return AuditDetailDTO(
            audit_id=audit_entity.id,
            url=audit_entity.url,
            status=audit_entity.status.value,
            platform=audit_entity.platform,
            overall_score=audit_entity.overall_score,
            severity_counts=audit_entity.severity_counts,
            created_at=audit_entity.created_at,
            completed_at=audit_entity.completed_at,
            error_message=audit_entity.error_message,
            protocol_results=audit_entity.protocol_results,
            schema_results=audit_entity.schema_results,
            content_results=audit_entity.content_results,
            edge_results=audit_entity.edge_results,
            bilingual_results=audit_entity.bilingual_results,
            issues=issues,
        )
