"""Schema Validation API Endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.schema_validator import (
    validate_product_schema,
    validate_bilingual_schemas,
    compare_visible_vs_structured
)

router = APIRouter()


class SchemaValidationRequest(BaseModel):
    jsonld: List[dict]


class VisibleVsStructuredRequest(BaseModel):
    visible_markdown: str
    jsonld: dict


class BilingualSchemaRequest(BaseModel):
    arabic_jsonld: List[dict]
    english_jsonld: List[dict]


@router.post("/validate")
async def validate_schema(request: SchemaValidationRequest):
    """
    Validate Product JSON-LD schema
    
    Checks:
    - Required fields (name, offers, price, currency)
    - AggregateOffer vs regular Offer
    - Middle East currency codes
    - Availability values
    """
    
    try:
        result = validate_product_schema(request.jsonld)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {str(e)}")


@router.post("/validate/visible-vs-structured")
async def validate_visible_vs_structured(request: VisibleVsStructuredRequest):
    """
    Compare visible page content with JSON-LD structured data
    
    Detects:
    - Price mismatches (hallucination risk)
    - Product name discrepancies
    """
    
    try:
        result = compare_visible_vs_structured(
            request.visible_markdown,
            request.jsonld
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/validate/bilingual")
async def validate_bilingual(request: BilingualSchemaRequest):
    """
    Validate bilingual schema consistency
    
    Checks:
    - Both language versions have Product schemas
    - Price consistency between AR/EN
    - Currency consistency
    - Metadata language matches page language
    """
    
    try:
        result = validate_bilingual_schemas(
            request.arabic_jsonld,
            request.english_jsonld
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bilingual validation failed: {str(e)}")
