from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.audit import AuditJob, AuditStatus
from app.schemas.audit import (
    AuditRequest,
    AuditResponse,
    AuditStatusResponse,
    AuditListResponse
)
from app.tasks.audit_tasks import run_audit_task

router = APIRouter(prefix="/audits")


@router.post("/", response_model=AuditResponse, status_code=201)
async def submit_audit(request: AuditRequest, db: Session = Depends(get_db)):
    """Submit a new AEO audit job"""
    
    # Create audit job in database
    audit_job = AuditJob(
        url=str(request.url),
        status=AuditStatus.QUEUED
    )
    db.add(audit_job)
    db.commit()
    db.refresh(audit_job)
    
    # Queue Celery task
    run_audit_task.delay(str(audit_job.id), {
        "include_bilingual": request.include_bilingual,
        "deep_content_analysis": request.deep_content_analysis
    })
    
    return AuditResponse(
        audit_id=audit_job.id,
        status=audit_job.status.value,
        estimated_time_seconds=45
    )


@router.get("/{audit_id}", response_model=AuditStatusResponse)
async def get_audit_status(audit_id: UUID, db: Session = Depends(get_db)):
    """Get audit job status and results"""
    
    audit_job = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
    
    if not audit_job:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return AuditStatusResponse(
        audit_id=audit_job.id,
        url=audit_job.url,
        status=audit_job.status.value,
        platform=audit_job.platform,
        overall_score=audit_job.overall_score,
        severity_counts=audit_job.severity_counts,
        created_at=audit_job.created_at,
        completed_at=audit_job.completed_at,
        error_message=audit_job.error_message,
        issues=[issue for issue in audit_job.issues]
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


@router.get("/", response_model=AuditListResponse)
async def list_audits(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List recent audits"""
    
    total = db.query(AuditJob).count()
    audits = (
        db.query(AuditJob)
        .order_by(AuditJob.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return AuditListResponse(
        audits=[
            AuditStatusResponse(
                audit_id=audit.id,
                url=audit.url,
                status=audit.status.value,
                platform=audit.platform,
                overall_score=audit.overall_score,
                severity_counts=audit.severity_counts,
                created_at=audit.created_at,
                completed_at=audit.completed_at,
                error_message=audit.error_message,
                issues=[]
            )
            for audit in audits
        ],
        total=total,
        limit=limit,
        offset=offset
    )
