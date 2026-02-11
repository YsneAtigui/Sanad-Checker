"""Unit tests for ProtocolService.

Tests protocol checking functionality with proper mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.protocol_standardized import ProtocolService
from app.application.dto import ProtocolResponse, ProtocolCheckResult
from app.domain.exceptions import ProtocolCheckError, ServiceUnavailableError
from app.domain.constants import STATUS_FOUND, STATUS_NOT_FOUND


@pytest.fixture
def protocol_service():
    """Create ProtocolService instance for testing."""
    return ProtocolService()


@pytest.fixture
def mock_protocol_result_success():
    """Mock successful protocol check result."""
    return {
        "llms_txt": {
            "status": "found",
            "content": "# LLMs.txt content",
            "valid_structure": True
        },
        "agent_card": {
            "status": "found",
            "schema_valid": True
        },
        "robots_txt": {
            "status": "found",
            "issues": []
        }
    }


@pytest.fixture
def mock_protocol_result_partial():
    """Mock partial protocol check result."""
    return {
        "llms_txt": {
            "status": "missing",
            "recommendation": "Add llms.txt file"
        },
        "agent_card": {
            "status": "found",
            "schema_valid": True
        },
        "robots_txt": {
            "status": "error",
            "issue": "Connection timeout"
        }
    }


@pytest.mark.asyncio
async def test_check_protocols_success(protocol_service, mock_protocol_result_success):
    """Test successful protocol check with all files found."""
    with patch('app.services.protocol_standardized._check_protocols_original',
               new_callable=AsyncMock, return_value=mock_protocol_result_success):
        
        result = await protocol_service.check_protocols("https://example.com")
        
        # Assert type
        assert isinstance(result, ProtocolResponse)
        
        # Assert score
        assert result.score == 100
        
        # Assert checks
        assert len(result.checks) == 3
        assert all(isinstance(check, ProtocolCheckResult) for check in result.checks)
        
        # Check llms.txt
        llms_check = next(c for c in result.checks if c.name == "llms.txt")
        assert llms_check.status == STATUS_FOUND
        assert llms_check.raw_content == "# LLMs.txt content"


@pytest.mark.asyncio
async def test_check_protocols_partial(protocol_service, mock_protocol_result_partial):
    """Test protocol check with some files missing."""
    with patch('app.services.protocol_standardized._check_protocols_original',
               new_callable=AsyncMock, return_value=mock_protocol_result_partial):
        
        result = await protocol_service.check_protocols("https://example.com")
        
        # Assert type
        assert isinstance(result, ProtocolResponse)
        
        # Assert score (1 out of 3 found)
        assert result.score == 33
        
        # Check that missing llms.txt is reflected
        llms_check = next(c for c in result.checks if c.name == "llms.txt")
        assert llms_check.status == STATUS_NOT_FOUND


@pytest.mark.asyncio
async def test_check_protocols_connection_error(protocol_service):
    """Test protocol check handling connection error."""
    with patch('app.services.protocol_standardized._check_protocols_original',
               new_callable=AsyncMock, side_effect=ConnectionError("Network unreachable")):
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await protocol_service.check_protocols("https://example.com")
        
        assert "Network unreachable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_protocols_generic_error(protocol_service):
    """Test protocol check handling generic error."""
    with patch('app.services.protocol_standardized._check_protocols_original',
               new_callable=AsyncMock, side_effect=ValueError("Invalid response")):
        
        with pytest.raises(ProtocolCheckError) as exc_info:
            await protocol_service.check_protocols("https://example.com")
        
        assert "Invalid response" in str(exc_info.value)


def test_map_status(protocol_service):
    """Test status mapping function."""
    assert protocol_service._map_status("found") == STATUS_FOUND
    assert protocol_service._map_status("missing") == STATUS_NOT_FOUND
    assert protocol_service._map_status("error") == STATUS_NOT_FOUND
    assert protocol_service._map_status("unknown") == STATUS_NOT_FOUND


def test_get_detail(protocol_service):
    """Test detail extraction function."""
    # Test with issue
    result = {"issue": "File not accessible"}
    assert protocol_service._get_detail(result) == "File not accessible"
    
    # Test with valid structure
    result = {"valid_structure": True}
    assert protocol_service._get_detail(result) == "File found and valid"
    
    # Test with issues list
    result = {"status": "found", "issues": ["Missing section A", "Missing section B"]}
    assert "Missing section A" in protocol_service._get_detail(result)
