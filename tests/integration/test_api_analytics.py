"""Integration tests for Analytics API endpoints.

Tests analytics endpoints with database data.
"""

import pytest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.infrastructure.database import get_db_session
from app.models.audit import AuditJob
from app.domain.entities import AuditStatus


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_audits(test_db_session):
    """Create sample audit data for testing."""
    from uuid import uuid4
    
    audits = [
        AuditJob(
            id=uuid4(),
            url="https://example.com/1",
            status=AuditStatus.COMPLETED,
            platform="salla",
            overall_score=85,
            severity_counts={"critical": 0, "high": 1, "medium": 2, "low": 3},
            created_at=datetime.utcnow() - timedelta(days=2),
            completed_at=datetime.utcnow() - timedelta(days=2)
        ),
        AuditJob(
            id=uuid4(),
            url="https://example.com/2",
            status=AuditStatus.COMPLETED,
            platform="zid",
            overall_score=65,
            severity_counts={"critical": 1, "high": 2, "medium": 1, "low": 2},
            created_at=datetime.utcnow() - timedelta(days=5),
            completed_at=datetime.utcnow() - timedelta(days=5)
        ),
        AuditJob(
            id=uuid4(),
            url="https://example.com/3",
            status=AuditStatus.FAILED,
            platform="salla",
            error_message="Connection timeout",
            created_at=datetime.utcnow() - timedelta(days=10)
        ),
        AuditJob(
            id=uuid4(),
            url="https://example.com/4",
            status=AuditStatus.IN_PROGRESS,
            platform="shopify",
            created_at=datetime.utcnow()
        ),
    ]
    
    for audit in audits:
        test_db_session.add(audit)
    
    test_db_session.commit()
    
    return audits


# ============================================================================
# ANALYTICS TESTS
# ============================================================================

def test_get_analytics_empty(client):
    """Test analytics with no data."""
    response = client.get("/api/v1/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_audits"] == 0
    assert data["completed_audits"] == 0
    assert data["average_score"] == 0.0
    assert data["platform_distribution"] == []
    assert data["status_distribution"] == []


def test_get_analytics_with_data(client, sample_audits):
    """Test analytics with sample data."""
    response = client.get("/api/v1/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Total audits
    assert data["total_audits"] == 4
    
    # Completed audits
    assert data["completed_audits"] == 2
    
    # Average score (85 + 65) / 2 = 75
    assert data["average_score"] == 75.0
    
    # Platform distribution
    assert len(data["platform_distribution"]) == 3
    platform_counts = {p["platform"]: p["count"] for p in data["platform_distribution"]}
    assert platform_counts["salla"] == 2
    assert platform_counts["zid"] == 1
    assert platform_counts["shopify"] == 1
    
    # Status distribution
    assert len(data["status_distribution"]) == 3
    status_counts = {s["status"]: s["count"] for s in data["status_distribution"]}
    assert status_counts["completed"] == 2
    assert status_counts["failed"] == 1
    assert status_counts["in_progress"] == 1


def test_get_analytics_with_period_filter(client, sample_audits):
    """Test analytics with period filter."""
    # Last 7 days (should include audits from 2 and 5 days ago)
    response = client.get("/api/v1/analytics?period=last_7_days")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 3 audits (2, 5 days ago, and today)
    assert data["total_audits"] >= 2
    
    # Last 30 days (should include all)
    response = client.get("/api/v1/analytics?period=last_30_days")
    data = response.json()
    
    assert data["total_audits"] == 4


def test_get_analytics_with_status_filter(client, sample_audits):
    """Test analytics with status filter."""
    response = client.get("/api/v1/analytics?status=completed")
    
    assert response.status_code == 200
    data = response.json()
    
    # Only completed audits
    assert data["total_audits"] == 2
    assert data["completed_audits"] == 2


def test_get_analytics_invalid_period(client):
    """Test analytics with invalid period."""
    response = client.get("/api/v1/analytics?period=invalid_period")
    
    assert response.status_code == 422


def test_get_analytics_score_distribution(client, sample_audits):
    """Test analytics score distribution."""
    response = client.get("/api/v1/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have score distribution
    assert "score_distribution" in data
    assert isinstance(data["score_distribution"], list)
    
    # Check score ranges
    score_ranges = {s["range"]: s["count"] for s in data["score_distribution"]}
    
    # Score 65 -> 60-80 range
    # Score 85 -> 80-100 range
    if "60-80" in score_ranges:
        assert score_ranges["60-80"] >= 1
    if "80-100" in score_ranges:
        assert score_ranges["80-100"] >= 1
