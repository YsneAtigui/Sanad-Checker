"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from typing import Generator
from uuid import uuid4
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.domain.entities import AuditEntity, AuditStatus
from app.infrastructure.persistence import SQLAlchemyAuditRepository


# Test database URL - using in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh test database session for each test.
    
    Uses in-memory SQLite for speed. Creates all tables before
    each test and tears them down after.
    """
    # Create engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def audit_repository(test_db: Session) -> SQLAlchemyAuditRepository:
    """Get audit repository with test database."""
    return SQLAlchemyAuditRepository(test_db)


@pytest.fixture
def sample_audit_entity() -> AuditEntity:
    """Create a sample audit entity for testing."""
    return AuditEntity(
        id=uuid4(),
        url="https://example.com/product/123",
        status=AuditStatus.QUEUED,
        created_at=datetime.utcnow(),
        platform="salla",
    )


@pytest.fixture
def completed_audit_entity() -> AuditEntity:
    """Create a completed audit entity for testing."""
    entity = AuditEntity(
        id=uuid4(),
        url="https://example.com/product/456",
        status=AuditStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        platform="zid",
        overall_score=85,
        severity_counts={"critical": 0, "high": 1, "medium": 2, "low": 3},
    )
    return entity
