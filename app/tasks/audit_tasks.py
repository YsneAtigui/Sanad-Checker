"""Celery Tasks for AEO Audit Pipeline

Complete implementation of audit orchestration with individual sub-tasks.
"""
import asyncio
from celery import chain, group
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import AuditJob, AuditStatus, AuditRecommendation, RecommendationSeverity, RecommendationCategory
from app.cache import redis_client
from datetime import datetime
from typing import Dict
import json


@celery_app.task(bind=True)
def run_audit_task(self, audit_id: str, options: dict):
    """
    Main audit orchestrator task - Full 10-step pipeline
    
    Steps:
    1. Extract page content
    2. Detect platform
    3. Check protocols (parallel with schema)
    4. Validate schema (parallel with protocols)
    5. Test edge visibility (parallel)
    6. Score content quality
    7. Generate recommendations
    8. Calculate sub-scores and overall score
    9. Generate report markdown
    10. Mark as completed, invalidate cache
    """
    
    db = SessionLocal()
    
    try:
        # Update status to in_progress
        audit = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        if not audit:
            raise ValueError(f"Audit {audit_id} not found")
        
        audit.status = AuditStatus.IN_PROGRESS
        db.commit()
        
        # Step 1-2: Extract page content and detect platform
        extraction_result = asyncio.run(extract_page_task(audit.url))
        
        if not extraction_result.get("success"):
            raise Exception(f"Page extraction failed: {extraction_result.get('error')}")
        
        audit.platform = extraction_result.get("platform", "Unknown")
        db.commit()
        
        # Step 3-5: Run parallel checks (protocols, schema, edge)
        protocol_future = asyncio.run(check_protocols_task(audit.url))
        schema_result = validate_schema_task(
            extraction_result.get("jsonld", []),
            extraction_result.get("markdown", "")
        )
        edge_future = asyncio.run(test_edge_visibility_task(audit.url))
        
        # Store parallel results
        audit.protocol_results = protocol_future
        audit.schema_results = schema_result
        audit.edge_results = edge_future
        db.commit()
        
        # Step 6: Score content quality
        content_result = asyncio.run(score_content_task(
            extraction_result.get("markdown", "")[:2000]
        ))
        audit.content_results = content_result
        db.commit()
        
        # Step 7: Generate recommendations
        generate_recommendations_task(audit_id, {
            "protocol": protocol_future,
            "schema": schema_result,
            "edge": edge_future,
            "content": content_result
        })
        
        # Step 8: Calculate scores
        audit = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        
        protocol_score = protocol_future.get("score", 0)
        schema_score = schema_result.get("score", 0)
        edge_score = edge_future.get("score", 0)
        content_score = content_result.get("score", 0)
        
        # Weighted average
        overall_score = round(
            (protocol_score * 0.30) +
            (schema_score * 0.25) +
            (edge_score * 0.10) +
            (content_score * 0.35)
        )
        
        audit.overall_score = overall_score
        
        # Count severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        # Count from recommendations
        for rec in audit.recommendations:
            severity = rec.severity.value.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        audit.severity_counts = severity_counts
        db.commit()
        
        # Step 9: Generate report markdown
        from app.services.report_generator import generate_markdown_report
        
        report_data = {
            "url": audit.url,
            "timestamp": audit.created_at.isoformat(),
            "overall_score": overall_score,
            "protocol": protocol_future,
            "schema": schema_result,
            "edge_visibility": edge_future,
            "content_quality": content_result,
            "issues": [
                {
                    "severity": rec.severity.value,
                    "title": rec.title,
                    "description": rec.description,
                    "recommendation": rec.code_example or rec.impact
                }
                for rec in audit.recommendations
            ]
        }
        
        markdown_report = generate_markdown_report(report_data)
        audit.report_markdown = markdown_report
        
        # Step 10: Mark as completed and invalidate cache
        audit.status = AuditStatus.COMPLETED
        audit.completed_at = datetime.utcnow()
        db.commit()
        
        # Invalidate caches
        redis_client.invalidate_audit_cache(str(audit_id))
        
        return {"status": "completed", "audit_id": str(audit_id), "score": overall_score}
        
    except Exception as e:
        # Mark as failed
        audit = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        if audit:
            audit.status = AuditStatus.FAILED
            audit.error_message = str(e)
            audit.completed_at = datetime.utcnow()
            db.commit()
        raise
    
    finally:
        db.close()


async def extract_page_task(url: str) -> Dict:
    """
    Extract page content using Crawl4AI
    
    Returns:
        Dictionary with markdown, html, jsonld, platform, media
    """
    from app.services.crawler import extract_page_content
    
    result = await extract_page_content(url)
    return result


async def check_protocols_task(url: str) -> Dict:
    """
    Check AEO protocol compliance
    
    Returns:
        Standardized protocol results with checks and score
    """
    from app.services.protocol_standardized import check_aeo_protocols_standardized
    
    result = await check_aeo_protocols_standardized(url)
    return result


def validate_schema_task(jsonld_data: list, visible_text: str = "") -> Dict:
    """
    Validate JSON-LD schema
    
    Returns:
        Standardized schema results with fields and score
    """
    from app.services.schema_standardized import validate_product_schema_standardized
    
    result = validate_product_schema_standardized(jsonld_data, visible_text)
    return result


async def test_edge_visibility_task(url: str) -> Dict:
    """
    Test AI agent accessibility
    
    Returns:
        Standardized edge results with agents, cloudflare detection, and score
    """
    from app.services.edge_standardized import test_edge_visibility_standardized
    
    result = await test_edge_visibility_standardized(url)
    return result


async def score_content_task(text: str) -> Dict:
    """
    Score content quality
    
    Returns:
        Standardized content results with AEO readiness, issues, and score
    """
    from app.services.content_standardized import score_content_standardized
    
    result = await score_content_standardized(text)
    return result


def generate_recommendations_task(audit_id: str, results: Dict) -> None:
    """
    Generate actionable recommendations based on audit results
    
    Creates AuditRecommendation records in database
    """
    db = SessionLocal()
    
    try:
        audit = db.query(AuditJob).filter(AuditJob.id == audit_id).first()
        if not audit:
            return
        
        recommendations = []
        
        # Protocol recommendations
        protocol = results.get("protocol", {})
        for check in protocol.get("checks", []):
            if check["status"] == "not_found":
                if check["name"] == "llms.txt":
                    recommendations.append(AuditRecommendation(
                        audit_job_id=audit_id,
                        severity=RecommendationSeverity.CRITICAL,
                        title="Missing llms.txt file",
                        description="Your site lacks the llms.txt file, preventing AI agents from discovering your content effectively.",
                        code_example="""# Create /llms.txt at your domain root:
# Sanad AEO Platform

> We help e-commerce brands optimize for AI search

## Sitemap
- /sitemap.xml

## Product Catalog
- /products""",
                        impact="AI agents like ChatGPT and Perplexity cannot index your site efficiently",
                        category=RecommendationCategory.PROTOCOL,
                        priority=1
                    ))
                elif check["name"] == "agent-card.json":
                    recommendations.append(AuditRecommendation(
                        audit_job_id=audit_id,
                        severity=RecommendationSeverity.WARNING,
                        title="Missing agent-card.json (Google A2A)",
                        description="No agent-card.json found for Google's Agentic AI protocol.",
                        code_example="""// Create /.well-known/agent-card.json:
{
  "schema": "https://schema.org/AgentCard",
  "name": "Your Store API",
  "endpoints": [
    {"path": "/api/products", "method": "GET"}
  ]
}""",
                        impact="Google's AI agents may not interact with your APIs",
                        category=RecommendationCategory.PROTOCOL,
                        priority=3
                    ))
        
        # Schema recommendations
        schema = results.get("schema", {})
        if schema.get("score", 0) < 70:
            recommendations.append(AuditRecommendation(
                audit_job_id=audit_id,
                severity=RecommendationSeverity.CRITICAL,
                title="Improve Product Schema",
                description=f"Schema score is {schema.get('score')}%. Missing or invalid fields detected.",
                code_example="""// Ensure your JSON-LD includes all required fields:
{
  "@type": "Product",
  "name": "Product Name",
  "offers": {
    "@type": "Offer",
    "price": "99.00",
    "priceCurrency": "SAR",
    "availability": "https://schema.org/InStock"
  },
  "brand": {"@type": "Brand", "name": "Your Brand"}
}""",
                impact="AI agents may show incomplete or incorrect product information",
                category=RecommendationCategory.SCHEMA,
                priority=2
            ))
        
        # Edge visibility recommendations
        edge = results.get("edge", {})
        blocked_count = sum(1 for agent in edge.get("agents", []) if agent["status"] == "blocked")
        if blocked_count > 0:
            recommendations.append(AuditRecommendation(
                audit_job_id=audit_id,
                severity=RecommendationSeverity.CRITICAL,
                title=f"{blocked_count} AI Agents Blocked",
                description=f"{blocked_count} out of 7 major AI agents cannot access your site.",
                code_example="# Check Cloudflare Bot Fight Mode settings\n# Whitelist AI agent user-agents:\n- GPTBot, ClaudeBot, CCBot, PerplexityBot",
                impact="Your products won't appear in AI-powered search results",
                category=RecommendationCategory.EDGE,
                priority=1
            ))
        
        # Content quality recommendations
        content = results.get("content", {})
        if content.get("aeo_readiness_score", 0) < 50:
            recommendations.append(AuditRecommendation(
                audit_job_id=audit_id,
                severity=RecommendationSeverity.WARNING,
                title="Improve Content AEO Readiness",
                description="Content lacks human-first, conversational tone suitable for AI agents.",
                code_example="Instead of: 'Best quality shoes cheap price buy now'\nUse: 'Handcrafted leather shoes combining comfort and style, perfect for daily wear.'",
                impact="AI agents may skip your content in favor of more natural-sounding alternatives",
                category=RecommendationCategory.CONTENT,
                priority=4
            ))
        
        # Save all recommendations
        for rec in recommendations:
            db.add(rec)
        
        db.commit()
        
    finally:
        db.close()
