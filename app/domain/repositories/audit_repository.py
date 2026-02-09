"""Repository interfaces for dependency inversion."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities import AuditEntity, AuditStatus


class IAuditRepository(ABC):
    """Interface for audit persistence operations.
    
    Following the Repository pattern for clean architecture.
    All implementations must conform to this interface.
    """
    
    @abstractmethod
    def create(self, audit: AuditEntity) -> AuditEntity:
        """Create a new audit.
        
        Args:
            audit: Audit entity to persist
            
        Returns:
            Created audit entity with ID
        """
        pass
    
    @abstractmethod
    def get_by_id(self, audit_id: UUID) -> Optional[AuditEntity]:
        """Retrieve audit by ID.
        
        Args:
            audit_id: UUID of the audit
            
        Returns:
            Audit entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, audit: AuditEntity) -> AuditEntity:
        """Update an existing audit.
        
        Args:
            audit: Audit entity with updated values
            
        Returns:
            Updated audit entity
        """
        pass
    
    @abstractmethod
    def delete(self, audit_id: UUID) -> bool:
        """Delete an audit.
        
        Args:
            audit_id: UUID of the audit to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
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
            Tuple of (list of audits, total count)
        """
        pass
