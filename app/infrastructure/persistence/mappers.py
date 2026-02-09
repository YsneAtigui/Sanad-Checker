"""Data mappers to convert between domain entities and ORM models."""

from typing import List
from uuid import UUID

from app.domain.entities import (
    AuditEntity,
    AuditIssueEntity,
    AuditStatus,
    IssueSeverity,
)
from app.models.audit import (
    AuditJob,
    AuditIssue,
    AuditStatus as ModelAuditStatus,
    IssueSeverity as ModelIssueSeverity,
)


def audit_model_to_entity(model: AuditJob) -> AuditEntity:
    """Convert ORM model to domain entity.
    
    Args:
        model: SQLAlchemy AuditJob model
        
    Returns:
        AuditEntity domain object
    """
    # Map issues
    issues = [issue_model_to_entity(issue) for issue in model.issues]
    
    return AuditEntity(
        id=model.id,
        url=model.url,
        status=AuditStatus(model.status.value),
        created_at=model.created_at,
        platform=model.platform,
        completed_at=model.completed_at,
        error_message=model.error_message,
        protocol_results=model.protocol_results,
        schema_results=model.schema_results,
        content_results=model.content_results,
        edge_results=model.edge_results,
        bilingual_results=model.bilingual_results,
        overall_score=model.overall_score,
        severity_counts=model.severity_counts,
        raw_html_path=model.raw_html_path,
        screenshot_path=model.screenshot_path,
        report_markdown=model.report_markdown,
        issues=issues,
    )


def audit_entity_to_model(entity: AuditEntity, existing_model: AuditJob = None) -> AuditJob:
    """Convert domain entity to ORM model.
    
    Args:
        entity: AuditEntity domain object
        existing_model: Optional existing model to update (for updates)
        
    Returns:
        SQLAlchemy AuditJob model
    """
    if existing_model:
        # Update existing model
        existing_model.url = entity.url
        existing_model.status = ModelAuditStatus(entity.status.value)
        existing_model.platform = entity.platform
        existing_model.completed_at = entity.completed_at
        existing_model.error_message = entity.error_message
        existing_model.protocol_results = entity.protocol_results
        existing_model.schema_results = entity.schema_results
        existing_model.content_results = entity.content_results
        existing_model.edge_results = entity.edge_results
        existing_model.bilingual_results = entity.bilingual_results
        existing_model.overall_score = entity.overall_score
        existing_model.severity_counts = entity.severity_counts
        existing_model.raw_html_path = entity.raw_html_path
        existing_model.screenshot_path = entity.screenshot_path
        existing_model.report_markdown = entity.report_markdown
        return existing_model
    else:
        # Create new model
        return AuditJob(
            id=entity.id,
            url=entity.url,
            status=ModelAuditStatus(entity.status.value),
            created_at=entity.created_at,
            platform=entity.platform,
            completed_at=entity.completed_at,
            error_message=entity.error_message,
            protocol_results=entity.protocol_results,
            schema_results=entity.schema_results,
            content_results=entity.content_results,
            edge_results=entity.edge_results,
            bilingual_results=entity.bilingual_results,
            overall_score=entity.overall_score,
            severity_counts=entity.severity_counts,
            raw_html_path=entity.raw_html_path,
            screenshot_path=entity.screenshot_path,
            report_markdown=entity.report_markdown,
        )


def issue_model_to_entity(model: AuditIssue) -> AuditIssueEntity:
    """Convert issue ORM model to domain entity.
    
    Args:
        model: SQLAlchemy AuditIssue model
        
    Returns:
        AuditIssueEntity domain object
    """
    return AuditIssueEntity(
        id=model.id,
        audit_job_id=model.audit_job_id,
        issue_type=model.issue_type,
        severity=IssueSeverity(model.severity.value),
        title=model.title,
        description=model.description,
        recommendation=model.recommendation,
        affected_field=model.affected_field,
        expected_value=model.expected_value,
        actual_value=model.actual_value,
    )


def issue_entity_to_model(entity: AuditIssueEntity) -> AuditIssue:
    """Convert issue domain entity to ORM model.
    
    Args:
        entity: AuditIssueEntity domain object
        
    Returns:
        SQLAlchemy AuditIssue model
    """
    return AuditIssue(
        id=entity.id,
        audit_job_id=entity.audit_job_id,
        issue_type=entity.issue_type,
        severity=ModelIssueSeverity(entity.severity.value),
        title=entity.title,
        description=entity.description,
        recommendation=entity.recommendation,
        affected_field=entity.affected_field,
        expected_value=entity.expected_value,
        actual_value=entity.actual_value,
    )
