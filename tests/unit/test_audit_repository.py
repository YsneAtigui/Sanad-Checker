"""Unit tests for audit repository implementation."""

import pytest
from uuid import uuid4

from app.domain.entities import AuditEntity, AuditStatus
from app.infrastructure.persistence import SQLAlchemyAuditRepository


@pytest.mark.unit
def test_create_audit(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity):
    """Test creating a new audit."""
    # Act
    created_audit = audit_repository.create(sample_audit_entity)
    
    # Assert
    assert created_audit.id == sample_audit_entity.id  
    assert created_audit.url == sample_audit_entity.url
    assert created_audit.status == AuditStatus.QUEUED
    assert created_audit.platform == "salla"


@pytest.mark.unit
def test_get_audit_by_id(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity):
    """Test retrieving audit by ID."""
    # Arrange
    created_audit = audit_repository.create(sample_audit_entity)
    
    # Act
    retrieved_audit = audit_repository.get_by_id(created_audit.id)
    
    # Assert
    assert retrieved_audit is not None
    assert retrieved_audit.id == created_audit.id
    assert retrieved_audit.url == created_audit.url


@pytest.mark.unit
def test_get_nonexistent_audit(audit_repository: SQLAlchemyAuditRepository):
    """Test retrieving non-existent audit returns None."""
    # Act
    audit = audit_repository.get_by_id(uuid4())
    
    # Assert
    assert audit is None


@pytest.mark.unit
def test_update_audit(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity):
    """Test updating an existing audit."""
    # Arrange
    created_audit = audit_repository.create(sample_audit_entity)
    created_audit.platform = "shopify"
    created_audit.overall_score = 90
    
    # Act
    updated_audit = audit_repository.update(created_audit)
    
    # Assert
    assert updated_audit.platform == "shopify"
    assert updated_audit.overall_score == 90


@pytest.mark.unit
def test_delete_audit(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity):
    """Test deleting an audit."""
    # Arrange
    created_audit = audit_repository.create(sample_audit_entity)
    
    # Act
    deleted = audit_repository.delete(created_audit.id)
    
    # Assert
    assert deleted is True
    assert audit_repository.get_by_id(created_audit.id) is None


@pytest.mark.unit
def test_delete_nonexistent_audit(audit_repository: SQLAlchemyAuditRepository):
    """Test deleting non-existent audit returns False."""
    # Act
    deleted = audit_repository.delete(uuid4())
    
    # Assert
    assert deleted is False


@pytest.mark.unit
def test_list_audits(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity, completed_audit_entity: AuditEntity):
    """Test listing audits with pagination."""
    # Arrange
    audit_repository.create(sample_audit_entity)
    audit_repository.create(completed_audit_entity)
    
    # Act
    audits, total = audit_repository.list_audits(limit=10, offset=0)
    
    # Assert
    assert total == 2
    assert len(audits) == 2


@pytest.mark.unit
def test_list_audits_with_status_filter(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity, completed_audit_entity: AuditEntity):
    """Test listing audits filtered by status."""
    # Arrange
    audit_repository.create(sample_audit_entity)
    audit_repository.create(completed_audit_entity)
    
    # Act
    audits, total = audit_repository.list_audits(status=AuditStatus.COMPLETED)
    
    # Assert
    assert total == 1
    assert audits[0].status == AuditStatus.COMPLETED


@pytest.mark.unit
def test_list_audits_with_platform_filter(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity, completed_audit_entity: AuditEntity):
    """Test listing audits filtered by platform."""
    # Arrange
    audit_repository.create(sample_audit_entity)
    audit_repository.create(completed_audit_entity)
    
    # Act
    audits, total = audit_repository.list_audits(platform="salla")
    
    # Assert
    assert total == 1
    assert audits[0].platform == "salla"


@pytest.mark.unit
def test_list_audits_pagination(audit_repository: SQLAlchemyAuditRepository, sample_audit_entity: AuditEntity, completed_audit_entity: AuditEntity):
    """Test pagination works correctly."""
    # Arrange
    audit_repository.create(sample_audit_entity)
    audit_repository.create(completed_audit_entity)
    
    # Act
    audits, total = audit_repository.list_audits(limit=1, offset=0)
    
    # Assert
    assert total == 2
    assert len(audits) == 1  # Only one audit due to limit
