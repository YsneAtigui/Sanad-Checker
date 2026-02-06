"""Content Scoring API Endpoints"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.services.content_scorer import score_product_content

router = APIRouter()


class ContentScoreRequest(BaseModel):
    text: str
    html: Optional[str] = None
    ollama_model: Optional[str] = "qwen3:8b"


@router.post("/score")
async def score_content(
    request: ContentScoreRequest,
    ollama_host: str = Query("http://localhost:11434", description="Ollama API endpoint")
):
    """
    Score content quality using Ollama LLM
    
    Analyzes:
    - Naturalness (human vs robotic)
    - Keyword stuffing
    - AEO readiness (Q&A structure)
    - Dialect usage (Khaliji authenticity)
    
    Returns:
    - Overall score (0-10)
    - Component scores
    - Robotic pattern detection
    - Actionable recommendations
    """
    
    try:
        result = await score_product_content(
            text=request.text,
            html=request.html,
            ollama_host=ollama_host,
            model=request.ollama_model
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content scoring failed: {str(e)}")
