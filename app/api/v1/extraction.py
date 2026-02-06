"""Content Extraction API Endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.crawler import extract_page_content, extract_bilingual_content

router = APIRouter()


class ExtractionRequest(BaseModel):
    url: HttpUrl


class ExtractionResponse(BaseModel):
    success: bool
    url: str
    platform: str | None = None
    markdown: str | None = None
    jsonld: list | None = None
    media: dict | None = None
    error: str | None = None


class BilingualExtractionResponse(BaseModel):
    arabic: ExtractionResponse
    english: ExtractionResponse


@router.post("/extract", response_model=ExtractionResponse)
async def extract_content(request: ExtractionRequest):
    """
    Extract clean, LLM-native content from a product page
    
    Returns:
    - Markdown content (filtered)
    - JSON-LD structured data
    - Media (images, videos)
    - Platform detection (Salla, Zid, Shopify)
    """
    
    try:
        result = await extract_page_content(str(request.url))
        
        return ExtractionResponse(
            success=result.get("success", False),
            url=result.get("url", str(request.url)),
            platform=result.get("platform"),
            markdown=result.get("markdown"),
            jsonld=result.get("jsonld"),
            media=result.get("media"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}")


@router.post("/extract/bilingual", response_model=BilingualExtractionResponse)
async def extract_bilingual(request: ExtractionRequest):
    """
    Extract both Arabic (/ar) and English (/en) versions of a page
    """
    
    try:
        result = await extract_bilingual_content(str(request.url))
        
        ar_data = result.get("arabic", {})
        en_data = result.get("english", {})
        
        return BilingualExtractionResponse(
            arabic=ExtractionResponse(
                success=ar_data.get("success", False),
                url=ar_data.get("url", ""),
                platform=ar_data.get("platform"),
                markdown=ar_data.get("markdown"),
                jsonld=ar_data.get("jsonld"),
                media=ar_data.get("media"),
                error=ar_data.get("error")
            ),
            english=ExtractionResponse(
                success=en_data.get("success", False),
                url=en_data.get("url", ""),
                platform=en_data.get("platform"),
                markdown=en_data.get("markdown"),
                jsonld=en_data.get("jsonld"),
                media=en_data.get("media"),
                error=en_data.get("error")
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bilingual extraction failed: {str(e)}")
