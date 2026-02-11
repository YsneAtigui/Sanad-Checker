"""Unit tests for ContentService.

Tests content quality analysis functionality with mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.content_standardized import ContentService
from app.application.dto import ContentResponse, ContentIssue
from app.domain.exceptions import ContentAnalysisError


@pytest.fixture
def content_service():
    """Create ContentService instance for testing."""
    return ContentService()


@pytest.fixture
def mock_ollama_result_good():
    """Mock good Ollama scoring result."""
    return {
        "overall_score": 8,  # 0-10 scale
        "robotic_patterns": {
            "has_issues": False,
            "issues": []
        }
    }


@pytest.fixture
def mock_ollama_result_poor():
    """Mock poor Ollama scoring result."""
    return {
        "overall_score": 3,
        "robotic_patterns": {
            "has_issues": True,
            "issues": [
                "Excessive use of marketing jargon",
                "Repetitive phrases detected",
                "Unnatural keyword placement"
            ]
        }
    }


@pytest.mark.asyncio
async def test_score_content_success(content_service, mock_ollama_result_good):
    """Test successful content scoring with good content."""
    text = "This premium widget offers exceptional value with its innovative design."
    
    with patch('app.services.content_standardized.score_product_content',
               new_callable=AsyncMock, return_value=mock_ollama_result_good):
        
        result = await content_service.score_content(text)
        
        # Assert type
        assert isinstance(result, ContentResponse)
        
        # Assert score (8 * 10 = 80)
        assert result.aeo_readiness_score == 80
        assert result.score == 80
        
        # Assert robotic pattern score
        assert result.robotic_pattern_score == "Low"
        
        # Assert minimal issues
        assert len(result.issues) == 0


@pytest.mark.asyncio
async def test_score_content_poor_quality(content_service, mock_ollama_result_poor):
    """Test content scoring with poor quality content."""
    text = "Buy now! Best price! Amazing deal! Click here!"
    
    with patch('app.services.content_standardized.score_product_content',
               new_callable=AsyncMock, return_value=mock_ollama_result_poor):
        
        result = await content_service.score_content(text)
        
        # Assert low score (3 * 10 = 30)
        assert result.aeo_readiness_score == 30
        
        # Assert high robotic pattern score (3 issues)
        assert result.robotic_pattern_score == "Medium"
        
        # Assert issues present
        assert len(result.issues) > 0
        
        # Check for low AEO readiness issue
        aeo_issue = next((i for i in result.issues if i.type == "low_aeo_readiness"), None)
        assert aeo_issue is not None
        assert aeo_issue.severity == "high"


@pytest.mark.asyncio
async def test_score_content_short_description(content_service, mock_ollama_result_good):
    """Test content scoring with very short description."""
    text = "Short"  # Less than MIN_DESCRIPTION_LENGTH
    
    with patch('app.services.content_standardized.score_product_content',
               new_callable=AsyncMock, return_value=mock_ollama_result_good):
        
        result = await content_service.score_content(text)
        
        # Check for short description issue
        short_issue = next((i for i in result.issues if i.type == "short_description"), None)
        assert short_issue is not None
        assert short_issue.severity == "medium"


@pytest.mark.asyncio
async def test_score_content_keyword_stuffing(content_service, mock_ollama_result_good):
    """Test content scoring with keyword stuffing detection."""
    # Create text with excessive repetition
    text = "widget " * 20 + "This is a widget for all your widget needs."
    
    with patch('app.services.content_standardized.score_product_content',
               new_callable=AsyncMock, return_value=mock_ollama_result_good):
        
        result = await content_service.score_content(text)
        
        # Check for keyword stuffing issue
        stuffing_issue = next((i for i in result.issues if i.type == "keyword_stuffing"), None)
        assert stuffing_issue is not None
        assert stuffing_issue.severity == "high"


@pytest.mark.asyncio
async def test_score_content_ollama_unavailable(content_service):
    """Test content scoring with Ollama unavailable (fallback)."""
    text = "Sample product description"
    
    with patch('app.services.content_standardized.score_product_content',
               new_callable=AsyncMock, side_effect=Exception("Ollama not running")):
        
        # Should not raise, should use fallback
        result = await content_service.score_content(text)
        
        # Assert fallback score (5 * 10 = 50)
        assert result.aeo_readiness_score == 50
        assert result.robotic_pattern_score == "Low"


def test_calculate_robotic_score(content_service):
    """Test robotic pattern score calculation."""
    # No issues
    result = {"robotic_patterns": {"has_issues": False}}
    assert content_service._calculate_robotic_score(result) == "Low"
    
    # 1 issue -> Low
    result = {"robotic_patterns": {"has_issues": True, "issues": ["Issue 1"]}}
    assert content_service._calculate_robotic_score(result) == "Low"
    
    # 3 issues -> Medium
    result = {"robotic_patterns": {"has_issues": True, "issues": ["1", "2", "3"]}}
    assert content_service._calculate_robotic_score(result) == "Medium"
    
    # 6 issues -> High
    result = {"robotic_patterns": {"has_issues": True, "issues": ["1", "2", "3", "4", "5", "6"]}}
    assert content_service._calculate_robotic_score(result) == "High"


def test_detect_keyword_stuffing(content_service):
    """Test keyword stuffing detection."""
    # Normal text
    text = "This is a normal product description with varied vocabulary."
    assert content_service._detect_keyword_stuffing(text) is False
    
    # Keyword stuffed text
    text = "widget " * 15 + "amazing product"
    assert content_service._detect_keyword_stuffing(text) is True
    
    # Empty text
    assert content_service._detect_keyword_stuffing("") is False
