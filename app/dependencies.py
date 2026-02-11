"""Dependency injection setup for FastAPI.

This module centralizes the creation of dependencies for proper
lifecycle management and testing.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db_session
from app.domain.repositories import IAuditRepository
from app.infrastructure.persistence import SQLAlchemyAuditRepository
from app.application.use_cases import (
    CreateAuditUseCase,
    GetAuditUseCase,
    ListAuditsUseCase,
)


# Repository Factory
def get_audit_repository(db: Session = Depends(get_db_session)) -> IAuditRepository:
    """Get audit repository instance.
    
    Args:
        db: Database session from dependency
        
    Returns:
        Configured audit repository
    """
    return SQLAlchemyAuditRepository(db)


# Service Factories
def get_protocol_service():
    """Get protocol checking service instance.
    
    Returns:
        Configured ProtocolService
    """
    from app.services.protocol_standardized import ProtocolService
    return ProtocolService()


def get_schema_service():
    """Get schema validation service instance.
    
    Returns:
        Configured SchemaService
    """
    from app.services.schema_standardized import SchemaService
    return SchemaService()


def get_content_service():
    """Get content quality service instance.
    
    Returns:
        Configured ContentService
    """
    from app.services.content_standardized import ContentService
    return ContentService()


def get_edge_service():
    """Get edge visibility service instance.
    
    Returns:
        Configured EdgeService
    """
    from app.services.edge_standardized import EdgeService
    return EdgeService()


# Use Case Factories
def get_create_audit_use_case(
    repository: IAuditRepository = Depends(get_audit_repository)
) -> CreateAuditUseCase:
    """Get create audit use case instance.
    
    Args:
        repository: Audit repository from dependency
        
    Returns:
        Configured create audit use case
    """
    return CreateAuditUseCase(repository)


def get_get_audit_use_case(
    repository: IAuditRepository = Depends(get_audit_repository)
) -> GetAuditUseCase:
    """Get audit retrieval use case instance.
    
    Args:
        repository: Audit repository from dependency
        
    Returns:
        Configured get audit use case
    """
    return GetAuditUseCase(repository)


def get_list_audits_use_case(
    repository: IAuditRepository = Depends(get_audit_repository)
) -> ListAuditsUseCase:
    """Get list audits use case instance.
    
    Args:
        repository: Audit repository from dependency
        
    Returns:
        Configured list audits use case
    """
    return ListAuditsUseCase(repository)
