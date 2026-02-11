"""Integration tests for Audit API endpoints.

Tests the full request/response cycle including database operations.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.infrastructure.database import get_db_session
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
            pass  # Session cleanup handled by fixture
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# CREATE AUDIT TESTS
# ============================================================================

def test_create_audit_success(client):
    """Test successful audit creation."""
    payload = {
        "url": "https://example.com/product/123",
        "include_bilingual": True,
        "deep_content_analysis": True
    }
    
    response = client.post("/api/v1/audits", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "audit_id" in data
    assert data["url"] == payload["url"]
    assert data["status"] == "queued"
    assert data["platform"] is None  # Not detected yet
    assert "created_at" in data


def test_create_audit_invalid_url(client):
    """Test audit creation with invalid URL."""
    payload = {
        "url": "not-a-valid-url",
        "include_bilingual": True
    }
    
    response = client.post("/api/v1/audits", json=payload)
    
    assert response.status_code == 422  # Validation error


def test_create_audit_missing_url(client):
    """Test audit creation without URL."""
    payload = {
        "include_bilingual": True
    }
    
    response = client.post("/api/v1/audits", json=payload)
    
    assert response.status_code == 422


# ============================================================================
# GET AUDIT TESTS
# ============================================================================

def test_get_audit_by_id(client):
    """Test retrieving audit by ID."""
    # Create audit first
    create_payload = {
        "url": "https://example.com/product/456"
    }
    create_response = client.post("/api/v1/audits", json=create_payload)
    audit_id = create_response.json()["audit_id"]
    
    # Get the audit
    response = client.get(f"/api/v1/audits/{audit_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["audit_id"] == audit_id
    assert data["url"] == create_payload["url"]
    assert data["status"] == "queued"


def test_get_audit_not_found(client):
    """Test retrieving non-existent audit."""
    fake_id = str(uuid4())
    
    response = client.get(f"/api/v1/audits/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_audit_invalid_uuid(client):
    """Test retrieving audit with invalid UUID."""
    response = client.get("/api/v1/audits/not-a-uuid")
    
    assert response.status_code == 422


# ============================================================================
# LIST AUDITS TESTS
# ============================================================================

def test_list_audits_empty(client):
    """Test listing audits when none exist."""
    response = client.get("/api/v1/audits")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["audits"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_audits_with_data(client):
    """Test listing audits with data."""
    # Create multiple audits
    for i in range(3):
        client.post("/api/v1/audits", json={
            "url": f"https://example.com/product/{i}"
        })
    
    response = client.get("/api/v1/audits")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["audits"]) == 3
    assert data["total"] == 3


def test_list_audits_with_pagination(client):
    """Test listing audits with pagination."""
    # Create 5 audits
    for i in range(5):
        client.post("/api/v1/audits", json={
            "url": f"https://example.com/product/{i}"
        })
    
    # Get first page
    response = client.get("/api/v1/audits?limit=2&offset=0")
    data = response.json()
    
    assert len(data["audits"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    
    # Get second page
    response = client.get("/api/v1/audits?limit=2&offset=2")
    data = response.json()
    
    assert len(data["audits"]) == 2
    assert data["offset"] == 2


def test_list_audits_with_status_filter(client):
    """Test listing audits with status filter."""
    # Create audits (all will be 'queued' initially)
    client.post("/api/v1/audits", json={"url": "https://example.com/1"})
    client.post("/api/v1/audits", json={"url": "https://example.com/2"})
    
    response = client.get("/api/v1/audits?status=queued")
    data = response.json()
    
    assert len(data["audits"]) == 2
    assert all(audit["status"] == "queued" for audit in data["audits"])
    
    # Test filter with no matches
    response = client.get("/api/v1/audits?status=completed")
    data = response.json()
    
    assert len(data["audits"]) == 0


def test_list_audits_with_platform_filter(client):
    """Test listing audits with platform filter."""
    # Note: Platform detection happens async, so this tests the filter logic
    response = client.get("/api/v1/audits?platform=salla")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should work even with 0 results
    assert isinstance(data["audits"], list)


def test_list_audits_invalid_status(client):
    """Test listing audits with invalid status."""
    response = client.get("/api/v1/audits?status=invalid_status")
    
    assert response.status_code == 422


# ============================================================================
# DELETE AUDIT TESTS
# ============================================================================

def test_delete_audit_success(client):
    """Test successful audit deletion."""
    # Create audit
    create_response = client.post("/api/v1/audits", json={
        "url": "https://example.com/delete-me"
    })
    audit_id = create_response.json()["audit_id"]
    
    # Delete the audit
    response = client.delete(f"/api/v1/audits/{audit_id}")
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/api/v1/audits/{audit_id}")
    assert get_response.status_code == 404


def test_delete_audit_not_found(client):
    """Test deleting non-existent audit."""
    fake_id = str(uuid4())
    
    response = client.delete(f"/api/v1/audits/{fake_id}")
    
    assert response.status_code == 404


# ============================================================================
# HEALTH CHECK TEST
# ============================================================================

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
