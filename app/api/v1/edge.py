"""Edge Visibility Testing API Endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.edge_visibility import comprehensive_edge_test, test_ai_agent_access

router = APIRouter()


class EdgeTestRequest(BaseModel):
    url: HttpUrl


@router.post("/test")
async def test_edge_visibility(request: EdgeTestRequest):
    """
    Comprehensive edge visibility test for AI agents
    
    Tests:
    - 6 major AI agents (GPTBot, ClaudeBot, etc.)
    - Cloudflare configuration
    - Bot challenges (reCAPTCHA, Turnstile, etc.)
    - User-Agent based blocking
    
    Returns severity levels and recommendations
    """
    
    try:
        result = await comprehensive_edge_test(str(request.url))
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edge visibility test failed: {str(e)}")


@router.post("/test/agents-only")
async def test_agents_only(request: EdgeTestRequest):
    """
    Test AI agent access only (faster, no Cloudflare analysis)
    """
    
    try:
        result = await test_ai_agent_access(str(request.url))
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent test failed: {str(e)}")
