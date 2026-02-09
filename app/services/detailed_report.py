"""
Enhanced Report Generator - Generate detailed structured reports

This module extends the existing report_generator.py with a new function
to generate structured, detailed reports that match the frontend TypeScript interfaces.
"""
from typing import Dict, List
from app.models import AuditJob


def generate_detailed_report(audit_job: AuditJob) -> Dict:
    """
    Generate detailed structured report matching frontend TypeScript interface
    
    Args:
        audit_job: Completed AuditJob with all results populated
        
    Returns:
        Structured report dictionary with all sections
    """
    
    # Calculate sub-scores
    protocol_score = _calculate_protocol_score(audit_job.protocol_results)
    schema_score = audit_job.schema_results.get("score", 0) if audit_job.schema_results else 0
    edge_score = audit_job.edge_results.get("score", 0) if audit_job.edge_results else 0
    content_score = audit_job.content_results.get("score", 0) if audit_job.content_results else 0
    
    report = {
        "audit_id": str(audit_job.id),
        "url": audit_job.url,
        "platform": audit_job.platform or "Unknown",
        "status": audit_job.status.value,
        "created_at": audit_job.created_at.isoformat() if audit_job.created_at else None,
        "completed_at": audit_job.completed_at.isoformat() if audit_job.completed_at else None,
        
        # Overall scoring
        "overall_score": audit_job.overall_score or 0,
        "sub_scores": {
            "protocol": protocol_score,
            "schema": schema_score,
            "edge": edge_score,
            "content": content_score
        },
        
        # Severity breakdown
        "severity_counts": audit_job.severity_counts or {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        
        # Detailed sections
        "protocol": _format_protocol_section(audit_job.protocol_results),
        "schema": _format_schema_section(audit_job.schema_results),
        "edge": _format_edge_section(audit_job.edge_results),
        "content": _format_content_section(audit_job.content_results),
        "bilingual": _format_bilingual_section(audit_job.bilingual_results),
        
        # Recommendations (from relationship)
        "recommendations": _format_recommendations(audit_job.recommendations)
    }
    
    return report


def _calculate_protocol_score(protocol_results: Dict) -> int:
    """Calculate protocol score from results"""
    if not protocol_results or not isinstance(protocol_results, dict):
        return 0
    
    checks = protocol_results.get("checks", [])
    if not checks:
        return 0
    
    passed = sum(1 for check in checks if check.get("status") in ["found", "valid"])
    return round((passed / len(checks)) * 100)


def _format_protocol_section(protocol_results: Dict) -> Dict:
    """Format protocol results for frontend"""
    if not protocol_results:
        return {"checks": [], "score": 0}
    
    # Ensure checks array exists with required fields
    checks = protocol_results.get("checks", [])
    formatted_checks = []
    
    for check in checks:
        formatted_checks.append({
            "name": check.get("name", ""),
            "status": check.get("status", "not_found"),  # found, not_found, invalid, valid
            "detail": check.get("detail", ""),
            "raw_content": check.get("raw_content", "")
        })
    
    return {
        "checks": formatted_checks,
        "score": protocol_results.get("score", 0)
    }


def _format_schema_section(schema_results: Dict) -> Dict:
    """Format schema validation results for frontend"""
    if not schema_results:
        return {
            "schema_type": "Product",
            "extracted_jsonld": "",
            "fields": [],
            "score": 0
        }
    
    # Format field comparisons
    fields = schema_results.get("fields", [])
    formatted_fields = []
    
    for field in fields:
        formatted_fields.append({
            "field": field.get("field", ""),
            "status": field.get("status", "missing"),  # match, mismatch, missing
            "visible_value": field.get("visible_value", ""),
            "structured_value": field.get("structured_value", "")
        })
    
    return {
        "schema_type": schema_results.get("schema_type", "Product"),
        "extracted_jsonld": schema_results.get("extracted_jsonld", ""),
        "fields": formatted_fields,
        "score": schema_results.get("score", 0)
    }


def _format_edge_section(edge_results: Dict) -> Dict:
    """Format edge visibility results for frontend"""
    if not edge_results:
        return {
            "agents": [],
            "cloudflare_detected": False,
            "bot_challenge_enabled": False,
            "score": 0
        }
    
    # AI agents array with exact names matching frontend
    agents = edge_results.get("agents", [])
    formatted_agents = []
    
    # Expected agent names from frontend
    expected_agents = ["ChatGPT", "Claude", "Perplexity", "Gemini", "Copilot", "You.com", "Jasper"]
    
    for agent in agents:
        formatted_agents.append({
            "name": agent.get("name", ""),
            "icon": agent.get("icon", ""),
            "status": agent.get("status", "unknown"),  # accessible, blocked, degraded
            "response_time_ms": agent.get("response_time_ms", 0),
            "data_completeness": agent.get("data_completeness", "None")  # Full, Partial, None
        })
    
    return {
        "agents": formatted_agents,
        "cloudflare_detected": edge_results.get("cloudflare_detected", False),
        "bot_challenge_enabled": edge_results.get("bot_challenge_enabled", False),
        "score": edge_results.get("score", 0)
    }


def _format_content_section(content_results: Dict) -> Dict:
    """Format content quality results for frontend"""
    if not content_results:
        return {
            "aeo_readiness_score": 0,
            "robotic_pattern_score": "Unknown",
            "issues": [],
            "score": 0
        }
    
    # Format content issues
    issues = content_results.get("issues", [])
    formatted_issues = []
    
    for issue in issues:
        formatted_issues.append({
            "type": issue.get("type", ""),
            "severity": issue.get("severity", "low"),
            "description": issue.get("description", ""),
            "location": issue.get("location", "")
        })
    
    return {
        "aeo_readiness_score": content_results.get("aeo_readiness_score", 0),
        "robotic_pattern_score": content_results.get("robotic_pattern_score", "Unknown"),  # Low, Medium, High
        "issues": formatted_issues,
        "score": content_results.get("score", 0)
    }


def _format_bilingual_section(bilingual_results: Dict) -> Dict:
    """Format bilingual analysis results"""
    if not bilingual_results:
        return {
            "has_arabic": False,
            "has_english": False,
            "consistency_score": 0,
            "issues": []
        }
    
    return {
        "has_arabic": bilingual_results.get("has_arabic", False),
        "has_english": bilingual_results.get("has_english", False),
        "consistency_score": bilingual_results.get("consistency_score", 0),
        "issues": bilingual_results.get("issues", [])
    }


def _format_recommendations(recommendations_list) -> List[Dict]:
    """Format recommendations from database relationship"""
    if not recommendations_list:
        return []
    
    formatted = []
    for rec in recommendations_list:
        formatted.append({
            "id": str(rec.id),
            "severity": rec.severity.value,
            "title": rec.title,
            "description": rec.description,
            "code_example": rec.code_example,
            "impact": rec.impact,
            "category": rec.category.value if rec.category else None,
            "priority": rec.priority
        })
    
    # Sort by priority (1 = highest)
    formatted.sort(key=lambda x: x.get("priority", 999))
    
    return formatted
