"""Unit tests for EdgeService.

Tests edge visibility and AI agent accessibility with mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.edge_standardized import EdgeService
from app.application.dto import EdgeResponse, AgentAccessResult
from app.domain.exceptions import ServiceUnavailableError


@pytest.fixture
def edge_service():
    """Create EdgeService instance for testing."""
    return EdgeService()


@pytest.fixture
def mock_httpx_response_success():
    """Mock successful HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.text = "A" * 6000  # Long content for full completeness
    response.headers = {}
    return response


@pytest.fixture
def mock_httpx_response_cloudflare():
    """Mock HTTP response with Cloudflare."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.text = "Cloudflare protection active" + ("A" * 5000)
    response.headers = {"cf-ray": "123456789"}
    return response


@pytest.fixture
def mock_httpx_response_blocked():
    """Mock blocked HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 403
    response.text = "Access denied - bot challenge"
    response.headers = {}
    return response


@pytest.mark.asyncio
async def test_edge_visibility_all_accessible(edge_service, mock_httpx_response_success):
    """Test edge visibility with all agents accessible."""
    async def mock_get(*args, **kwargs):
        return mock_httpx_response_success
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await edge_service.test_visibility("https://example.com")
        
        # Assert type
        assert isinstance(result, EdgeResponse)
        
        # Assert score (7/7 accessible = 100%)
        assert result.score == 100
        
        # Assert all 7 agents tested
        assert len(result.agents) == 7
        assert all(isinstance(agent, AgentAccessResult) for agent in result.agents)
        
        # Check all accessible
        assert all(agent.status == "accessible" for agent in result.agents)
        
        # Check no Cloudflare or bot challenges
        assert result.cloudflare_detected == False
        assert result.bot_challenge_enabled == False


@pytest.mark.asyncio
async def test_edge_visibility_with_cloudflare(edge_service, mock_httpx_response_cloudflare):
    """Test edge visibility with Cloudflare detected."""
    async def mock_get(*args, **kwargs):
        return mock_httpx_response_cloudflare
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await edge_service.test_visibility("https://example.com")
        
        # Assert Cloudflare detected
        assert result.cloudflare_detected == True
        
        # Still accessible
        assert result.score == 100


@pytest.mark.asyncio
async def test_edge_visibility_with_blocking(edge_service, mock_httpx_response_blocked):
    """Test edge visibility with bot blocking."""
    async def mock_get(*args, **kwargs):
        return mock_httpx_response_blocked
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await edge_service.test_visibility("https://example.com")
        
        # Assert bot challenge detected
        assert result.bot_challenge_enabled == True
        
        # Assert low score (0/7 accessible = 0%)
        assert result.score == 0
        
        # Check all blocked
        assert all(agent.status == "blocked" for agent in result.agents)
        assert all(agent.data_completeness == "None" for agent in result.agents)


@pytest.mark.asyncio
async def test_edge_visibility_mixed_results(edge_service):
    """Test edge visibility with mixed accessibility."""
    call_count = 0
    
    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        response = MagicMock(spec=httpx.Response)
        if call_count <= 3:
            # First 3 successful
            response.status_code = 200
            response.text = "Good content" * 1000
            response.headers = {}
        elif call_count <= 5:
            # Next 2 blocked
            response.status_code = 403
            response.text = "Blocked"
            response.headers = {}
        else:
            # Last 2 degraded
            response.status_code = 500
            response.text = "Error"
            response.headers = {}
        return response
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await edge_service.test_visibility("https://example.com")
        
        # 3 accessible out of 7 = ~43%
        assert 40 <= result.score <= 45
        
        # Check mix of statuses
        statuses = {agent.status for agent in result.agents}
        assert "accessible" in statuses
        assert "blocked" in statuses or "degraded" in statuses


@pytest.mark.asyncio
async def test_edge_visibility_connection_errors(edge_service):
    """Test edge visibility with connection errors."""
    async def mock_get(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        result = await edge_service.test_visibility("https://example.com")
        
        # Assert all blocked due to errors
        assert result.score == 0
        assert all(agent.status == "blocked" for agent in result.agents)
        assert all(agent.response_time_ms == 0 for agent in result.agents)


@pytest.mark.asyncio
async def test_edge_visibility_service_failure(edge_service):
    """Test edge visibility with complete service failure."""
    with patch('httpx.AsyncClient', side_effect=Exception("Client creation failed")):
        
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await edge_service.test_visibility("https://example.com")
        
        assert "Edge Visibility Test" in str(exc_info.value)


def test_edge_service_agent_list(edge_service):
    """Test that EdgeService has correct agent list."""
    assert len(edge_service.AI_AGENTS) == 7
    
    # Check required agents
    agent_names = {agent["name"] for agent in edge_service.AI_AGENTS}
    assert "ChatGPT" in agent_names
    assert "Claude" in agent_names
    assert "Perplexity" in agent_names
    assert "Gemini" in agent_names
    
    # Check all have required fields
    for agent in edge_service.AI_AGENTS:
        assert "name" in agent
        assert "icon" in agent
        assert "user_agent" in agent
