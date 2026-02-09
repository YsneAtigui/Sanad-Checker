from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from typing import List, Optional
from uuid import UUID

from app.schemas.audit import (
    AuditRequest,
    AuditResponse,
    AuditStatusResponse,
    AuditListResponse
)
from app.application.dto import (
    CreateAuditDTO,
    PaginationDTO,
    ListAuditsDTO,
)
from app.application.use_cases import (
    CreateAuditUseCase,
    GetAuditUseCase,
    ListAuditsUseCase,
)
from app.dependencies import (
    get_create_audit_use_case,
    get_get_audit_use_case,
    get_list_audits_use_case,
)

# Legacy imports for non-refactored endpoints (TODO: refactor these)
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditJob, AuditStatus

from app.tasks.audit_tasks import run_audit_task
from app.cache import redis_client
from app.config import settings

router = APIRouter(prefix="/audits")


@router.post("/", response_model=AuditResponse, status_code=201)
async def submit_audit(
    request: AuditRequest,
    use_case: CreateAuditUseCase = Depends(get_create_audit_use_case)
):
    """Submit a new AEO audit job using clean architecture.
    
    This endpoint uses dependency injection to get the use case,
    which handles all business logic and persistence.
    """
    try:
        # Create DTO from request
        dto = CreateAuditDTO(
            url=str(request.url),
            include_bilingual=request.include_bilingual,
            deep_content_analysis=request.deep_content_analysis
        )
        
        # Execute use case
        audit_dto = use_case.execute(dto)
        
        # Queue Celery task
        run_audit_task.delay(str(audit_dto.audit_id), {
            "include_bilingual": request.include_bilingual,
            "deep_content_analysis": request.deep_content_analysis
        })
        
        return AuditResponse(
            audit_id=audit_dto.audit_id,
            status=audit_dto.status,
            estimated_time_seconds=45
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{audit_id}", response_model=AuditStatusResponse)
async def get_audit_status(
    audit_id: UUID,
    use_case: GetAuditUseCase = Depends(get_get_audit_use_case)
):
    """Get audit job status and results using clean architecture."""
    
    audit_dto = use_case.execute(audit_id)
    
    if not audit_dto:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return AuditStatusResponse(
        audit_id=audit_dto.audit_id,
        url=audit_dto.url,
        status=audit_dto.status,
        platform=audit_dto.platform,
        overall_score=audit_dto.overall_score,
        severity_counts=audit_dto.severity_counts,
        created_at=audit_dto.created_at,
        completed_at=audit_dto.completed_at,
        error_message=audit_dto.error_message,
        issues=audit_dto.issues
    )


@router.get("/{audit_id}/report")
async def get_audit_report(
    audit_id: UUID,
    format: str = "markdown",
    db: Session = Depends(get_db)
):
    """Get formatted audit report"""
    
    audit_job = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
    
    if not audit_job:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    if audit_job.status != AuditStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Audit not completed yet")
    
    if format == "json":
        return {
            "audit_id": audit_job.id,
            "url": audit_job.url,
            "score": audit_job.overall_score,
            "protocol_results": audit_job.protocol_results,
            "schema_results": audit_job.schema_results,
            "content_results": audit_job.content_results,
            "edge_results": audit_job.edge_results,
            "bilingual_results": audit_job.bilingual_results,
            "issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "recommendation": issue.recommendation
                }
                for issue in audit_job.issues
            ]
        }
    else:  # markdown
        return PlainTextResponse(
            content=audit_job.report_markdown or "Report not generated",
            media_type="text/markdown"
        )


@router.get("/{audit_id}/detailed")
async def get_detailed_report(
    audit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed structured report matching frontend TypeScript interfaces
    
    Returns complete audit report with:
    - Protocol checks with raw content
    - Schema validation with visible vs structured comparison
    - AI agent accessibility with response times
    - Content quality with issues
    - Bilingual analysis
    - Prioritized recommendations with code examples
    """
    
    # Check cache first
    cache_key = f"audit_detail:{audit_id}"
    cached = redis_client.get_cached(cache_key)
    
    if cached:
        return cached
    
    # Fetch from database
    audit_job = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
    
    if not audit_job:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    if audit_job.status != AuditStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Audit not completed yet")
    
    # Generate detailed report using service
    from app.services.detailed_report import generate_detailed_report
    
    detailed_report = generate_detailed_report(audit_job)
    
    # Cache for 1 hour
    redis_client.set_cached(cache_key, detailed_report, settings.CACHE_TTL_AUDIT)
    
    return detailed_report


@router.get("/", response_model=AuditListResponse)
async def list_audits(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, regex="^(queued|in_progress|completed|failed)$"),
    platform: Optional[str] = Query(None),
    use_case: ListAuditsUseCase = Depends(get_list_audits_use_case)
):
    """
    List recent audits with optional filtering using clean architecture.
    
    **Query params:**
    - limit: Number of results (1-100, default: 20)
    - offset: Pagination offset (default: 0)
    - status: Filter by status (queued, in_progress, completed, failed)
    - platform: Filter by platform (salla, zid, shopify, etc.)
    """
    try:
        # Check cache
        cache_key = f"audits:list:{limit}:{offset}:{status}:{platform}"
        cached = redis_client.get_cached(cache_key)
        
        if cached:
            return cached
        
        # Create DTO
        dto = ListAuditsDTO(
            pagination=PaginationDTO(limit=limit, offset=offset),
            status=status,
            platform=platform
        )
        
        # Execute use case
        result = use_case.execute(dto)
        
        # Convert to response format
        response = AuditListResponse(
            audits=[
                AuditStatusResponse(
                    audit_id=audit.audit_id,
                    url=audit.url,
                    status=audit.status,
                    platform=audit.platform,
                    overall_score=audit.overall_score,
                    severity_counts=audit.severity_counts,
                    created_at=audit.created_at,
                    completed_at=audit.completed_at,
                    error_message=audit.error_message,
                    issues=[]
                )
                for audit in result.audits
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset
        )
        
        # Cache for 1 minute
        redis_client.set_cached(cache_key, response.dict(), settings.CACHE_TTL_LIST)
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{audit_id}")
async def delete_audit(
    audit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an audit job and all related data
    
    **This will:**
    - Delete the audit record
    - Cascade delete all issues and recommendations
    - Invalidate all related caches
    - Remove from analytics calculations
    """
    
    audit_job = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
    
    if not audit_job:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Delete audit (cascade will handle issues and recommendations)
    db.delete(audit_job)
    db.commit()
    
    # Invalidate all related caches
    redis_client.invalidate_audit_cache(str(audit_id))
    
    return {
        "status": "success",
        "message": f"Audit {audit_id} deleted successfully",
        "audit_id": str(audit_id)
    }


@router.post("/{audit_id}/rescan", response_model=AuditResponse, status_code=201)
async def rescan_audit(
    audit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Re-scan an existing audit (creates a new audit with same URL)
    
    **This will:**
    - Create a new audit job with the same URL
    - Queue a new Celery task
    - Return the new audit ID
    
    **Note:** The original audit remains unchanged
    """
    
    # Fetch original audit
    original_audit = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
    
    if not original_audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Create new audit job with same URL
    new_audit = AuditJob(
        url=original_audit.url,
        status=AuditStatus.QUEUED
    )
    db.add(new_audit)
    db.commit()
    db.refresh(new_audit)
    
    # Queue Celery task
    run_audit_task.delay(str(new_audit.id), {
        "include_bilingual": True,
        "deep_content_analysis": True
    })
    
    return AuditResponse(
        audit_id=new_audit.id,
        status=new_audit.status.value,
        estimated_time_seconds=45
    )

