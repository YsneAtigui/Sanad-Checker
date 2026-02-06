"""Report Generation API Endpoints"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from typing import Optional
from app.services.report_generator import generate_full_audit_report, generate_markdown_report

router = APIRouter()


class AuditReportRequest(BaseModel):
    url: HttpUrl
    ollama_model: Optional[str] = "qwen3:8b"


@router.post("/generate")
async def generate_audit_report(
    request: AuditReportRequest,
    ollama_host: str = Query("http://localhost:11434", description="Ollama API endpoint")
):
    """
    Generate comprehensive AEO audit report
    
    Orchestrates all services:
    - Protocol checker (llms.txt, agent-card.json, robots.txt)
    - Content extractor (bilingual)
    - Schema validator (Product JSON-LD)
    - Edge visibility tester (AI agent blocking)
    - Content quality scorer (with Ollama)
    
    Returns:
    - Overall AEO score (0-100)
    - Classified issues by severity
    - Detailed findings from all checks
    - Actionable recommendations
    """
    
    try:
        report = await generate_full_audit_report(
            url=str(request.url),
            ollama_host=ollama_host
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/generate/markdown")
async def generate_markdown_audit_report(
    request: AuditReportRequest,
    ollama_host: str = Query("http://localhost:11434", description="Ollama API endpoint")
):
    """
    Generate audit report in Markdown format
    """
    
    try:
        report = await generate_full_audit_report(
            url=str(request.url),
            ollama_host=ollama_host
        )
        
        markdown = generate_markdown_report(report)
        
        return {
            "report": report,
            "markdown": markdown
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Markdown report generation failed: {str(e)}")
