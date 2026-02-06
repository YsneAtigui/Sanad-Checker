"""Protocol Checker API Endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.protocol import check_aeo_protocols

router = APIRouter()


class ProtocolCheckRequest(BaseModel):
    url: HttpUrl


class ProtocolCheckResponse(BaseModel):
    url: str
    llms_txt: dict
    agent_card: dict
    robots_txt: dict


@router.post("/check", response_model=ProtocolCheckResponse)
async def check_protocols(request: ProtocolCheckRequest):
    """
    Check AEO protocol compliance for a given URL
    
    Validates:
    - llms.txt presence and structure
    - agent-card.json (Google A2A protocol)
    - robots.txt AI agent rules
    """
    
    try:
        results = await check_aeo_protocols(str(request.url))
        
        return ProtocolCheckResponse(
            url=str(request.url),
            llms_txt=results["llms_txt"],
            agent_card=results["agent_card"],
            robots_txt=results["robots_txt"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Protocol check failed: {str(e)}")
