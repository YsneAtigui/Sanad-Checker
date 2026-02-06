"""AEO Audit Report Generator Service

Orchestrates all services to generate comprehensive AEO audit reports.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from app.services.protocol import check_aeo_protocols
from app.services.crawler import extract_bilingual_content
from app.services.schema_validator import (
    validate_product_schema,
    validate_bilingual_schemas,
    compare_visible_vs_structured
)
from app.services.edge_visibility import comprehensive_edge_test
from app.services.content_scorer import score_product_content


async def generate_full_audit_report(url: str, ollama_host: str = "http://localhost:11434") -> Dict:
    """
    Generate complete AEO audit report by running all services
    
    Args:
        url: URL to audit
        ollama_host: Ollama endpoint for content scoring
    
    Returns:
        Complete audit report with all findings
    """
    
    report = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "protocol": {},
        "extraction": {},
        "schema": {},
        "edge_visibility": {},
        "content_quality": {},
        "bilingual": {},
        "issues": [],
        "overall_score": 0,
        "severity": "none"
    }
    
    try:
        # Run all checks concurrently where possible
        results = await asyncio.gather(
            check_aeo_protocols(url),
            extract_bilingual_content(url),
            comprehensive_edge_test(url),
            return_exceptions=True
        )
        
        protocol_result, extraction_result, edge_result = results
        
        # Store results
        if not isinstance(protocol_result, Exception):
            report["protocol"] = protocol_result
        
        if not isinstance(extraction_result, Exception):
            report["extraction"] = extraction_result
            
            # Schema validation (depends on extraction)
            ar_data = extraction_result.get("arabic", {})
            en_data = extraction_result.get("english", {})
            
            if ar_data.get("success") and ar_data.get("jsonld"):
                schema_result = validate_product_schema(ar_data["jsonld"])
                report["schema"] = schema_result
                
                # Visible vs structured comparison
                if ar_data.get("markdown"):
                    visible_vs_structured = compare_visible_vs_structured(
                        ar_data["markdown"],
                        ar_data["jsonld"][0] if ar_data["jsonld"] else {}
                    )
                    report["schema"]["visible_vs_structured"] = visible_vs_structured
            
            # Bilingual schema consistency
            if (ar_data.get("success") and ar_data.get("jsonld") and 
                en_data.get("success") and en_data.get("jsonld")):
                bilingual_result = validate_bilingual_schemas(
                    ar_data["jsonld"],
                    en_data["jsonld"]
                )
                report["bilingual"] = bilingual_result
            
            # Content quality scoring (Arabic version)
            if ar_data.get("success") and ar_data.get("markdown"):
                content_score = await score_product_content(
                    text=ar_data["markdown"][:2000],  # Limit text length
                    ollama_host=ollama_host
                )
                report["content_quality"] = content_score
        
        if not isinstance(edge_result, Exception):
            report["edge_visibility"] = edge_result
        
        # Collect issues and calculate score
        issues = collect_all_issues(report)
        report["issues"] = issues
        
        overall_score = calculate_overall_score(report)
        report["overall_score"] = overall_score
        report["severity"] = determine_overall_severity(issues)
        
        return report
        
    except Exception as e:
        report["error"] = str(e)
        report["severity"] = "critical"
        return report


def collect_all_issues(report: Dict) -> List[Dict]:
    """
    Collect and classify all issues from audit results
    
    Args:
        report: Audit report data
    
    Returns:
        List of classified issues
    """
    
    issues = []
    
    # Protocol issues
    protocol = report.get("protocol", {})
    
    if protocol.get("llms_txt", {}).get("status") == "not_found":
        issues.append({
            "type": "missing_llms_txt",
            "severity": "high",
            "title": "Missing llms.txt file",
            "description": "No llms.txt file found. AI agents may not discover your content.",
            "recommendation": "Create /llms.txt with your sitemap URL and content index.",
            "category": "protocol"
        })
    
    if protocol.get("agent_card", {}).get("status") == "not_found":
        issues.append({
            "type": "missing_agent_card",
            "severity": "medium",
            "title": "Missing agent-card.json (Google A2A)",
            "description": "No agent-card.json found for Google's Agentic AI protocol.",
            "recommendation": "Create /.well-known/agent-card.json with your API metadata.",
            "category": "protocol"
        })
    
    # Edge visibility issues
    edge = report.get("edge_visibility", {})
    if edge.get("summary", {}).get("blocked_agents", 0) > 0:
        blocked_count = edge["summary"]["blocked_agents"]
        issues.append({
            "type": "ai_agent_blocked",
            "severity": "critical",
            "title": f"{blocked_count} AI agents blocked",
            "description": f"{blocked_count} out of 6 major AI agents cannot access your site.",
            "recommendation": "Check Cloudflare Bot Fight Mode settings and reCAPTCHA configuration.",
            "category": "accessibility"
        })
    
    # Schema issues
    schema = report.get("schema", {})
    if not schema.get("schema_found"):
        issues.append({
            "type": "missing_jsonld",
            "severity": "high",
            "title": "No Product schema found",
            "description": "Missing JSON-LD Product schema for structured data.",
            "recommendation": "Add Product schema with proper offers, price, and availability.",
            "category": "schema"
        })
    elif not schema.get("valid"):
        for error in schema.get("errors", []):
            issues.append({
                "type": "schema_validation_error",
                "severity": "high",
                "title": "Product schema validation error",
                "description": error,
                "recommendation": "Fix the schema validation error.",
                "category": "schema"
            })
    
    # Visible vs structured data issues
    visible_vs = schema.get("visible_vs_structured", {})
    if not visible_vs.get("matches") and visible_vs.get("severity") in ["critical", "high"]:
        issues.append({
            "type": "price_mismatch",
            "severity": visible_vs.get("severity", "high"),
            "title": "Price mismatch detected",
            "description": "Visible price doesn't match JSON-LD structured data (hallucination risk).",
            "recommendation": "Ensure visible prices match exactly with schema prices.",
            "category": "schema"
        })
    
    # Bilingual issues
    bilingual = report.get("bilingual", {})
    if not bilingual.get("consistent") and bilingual.get("severity") in ["critical", "high", "medium"]:
        for issue_desc in bilingual.get("issues", []):
            issues.append({
                "type": "bilingual_inconsistency",
                "severity": bilingual.get("severity", "medium"),
                "title": "Bilingual schema inconsistency",
                "description": issue_desc,
                "recommendation": "Ensure Arabic and English schemas have consistent prices and metadata.",
                "category": "bilingual"
            })
    
    # Content quality issues
    content = report.get("content_quality", {})
    if content.get("overall_score", 10) < 5:
        issues.append({
            "type": "poor_content_quality",
            "severity": "critical" if content["overall_score"] < 3 else "high",
            "title": "Poor content quality",
            "description": content.get("recommendation", "Content needs improvement."),
            "recommendation": "Rewrite content to be more human-first and conversational.",
            "category": "content",
            "score": content.get("overall_score")
        })
    elif content.get("robotic_patterns", {}).get("has_issues"):
        issues.append({
            "type": "robotic_patterns",
            "severity": "medium",
            "title": "Robotic content patterns detected",
            "description": f"Found {len(content['robotic_patterns'].get('issues', []))} robotic patterns.",
            "recommendation": "Remove keyword stuffing and make content more natural.",
            "category": "content"
        })
    
    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: severity_order.get(x.get("severity"), 4))
    
    return issues


def calculate_overall_score(report: Dict) -> int:
    """
    Calculate 0-100 AEO score based on all audit results
    
    Args:
        report: Audit report data
    
    Returns:
        Overall score (0-100)
    """
    
    weights = {
        "protocol": 30,      # llms.txt, agent-card, robots.txt
        "schema": 25,        # JSON-LD validity
        "content": 20,       # Human-first score
        "bilingual": 15,     # Language consistency
        "accessibility": 10  # AI agent access
    }
    
    scores = {}
    
    # Protocol score
    protocol = report.get("protocol", {})
    protocol_passed = 0
    protocol_total = 3
    
    if protocol.get("llms_txt", {}).get("status") in ["found", "valid"]:
        protocol_passed += 1
    if protocol.get("agent_card", {}).get("status") in ["found", "valid"]:
        protocol_passed += 1
    if protocol.get("robots_txt", {}).get("status") in ["found", "valid"]:
        protocol_passed += 1
    
    scores["protocol"] = (protocol_passed / protocol_total) * 100
    
    # Schema score
    schema = report.get("schema", {})
    if schema.get("valid"):
        scores["schema"] = 100
    elif schema.get("schema_found"):
        scores["schema"] = 50  # Found but invalid
    else:
        scores["schema"] = 0
    
    # Content score (0-10 scale to 0-100)
    content = report.get("content_quality", {})
    scores["content"] = content.get("overall_score", 0) * 10
    
    # Bilingual score
    bilingual = report.get("bilingual", {})
    if bilingual.get("consistent"):
        scores["bilingual"] = 100
    elif bilingual:
        scores["bilingual"] = 50  # Exists but inconsistent
    else:
        scores["bilingual"] = 70  # Not applicable (monolingual)
    
    # Accessibility score
    edge = report.get("edge_visibility", {})
    blocked_agents = edge.get("summary", {}).get("blocked_agents", 0)
    total_agents = edge.get("summary", {}).get("total_agents_tested", 6)
    
    if total_agents > 0:
        scores["accessibility"] = ((total_agents - blocked_agents) / total_agents) * 100
    else:
        scores["accessibility"] = 50  # Unknown
    
    # Weighted average
    overall = sum(scores[k] * (weights[k] / 100) for k in weights)
    
    return round(overall)


def determine_overall_severity(issues: List[Dict]) -> str:
    """Determine overall severity based on issues"""
    
    if any(i.get("severity") == "critical" for i in issues):
        return "critical"
    elif any(i.get("severity") == "high" for i in issues):
        return "high"
    elif any(i.get("severity") == "medium" for i in issues):
        return "medium"
    else:
        return "low" if len(issues) > 0 else "none"


def generate_markdown_report(report: Dict) -> str:
    """
    Generate Markdown format report
    
    Args:
        report: Audit report data
    
    Returns:
        Markdown formatted report
    """
    
    score = report.get("overall_score", 0)
    score_emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "🔴"
    
    issues = report.get("issues", [])
    critical_issues = [i for i in issues if i.get("severity") == "critical"]
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]
    low_issues = [i for i in issues if i.get("severity") == "low"]
    
    # Build report
    md = f"""# AEO Audit Report

**URL:** {report.get('url')}  
**Audit Date:** {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M')}  
**Overall Score:** {score}/100 {score_emoji}

## Executive Summary

"""
    
    # Generate summary based on score and issues
    if len(critical_issues) > 0:
        md += f"""This site has **{len(critical_issues)} critical issue(s)** blocking AI agent visibility. Immediate action required to enable Answer Engine indexing.

Overall AEO score: {score}/100. Priority should be given to resolving critical blockers before optimizing other aspects.
"""
    elif score >= 80:
        md += f"""This site is well-optimized for Answer Engine visibility with a score of {score}/100. Minor improvements recommended.

No critical issues detected. The site follows AEO best practices and is accessible to major AI agents.
"""
    else:
        md += f"""This site requires optimization for Answer Engine visibility (score: {score}/100). {len(high_issues)} high-priority issue(s) detected.

While not critically blocked, significant improvements are needed to maximize AI agent discoverability.
"""
    
    # Add issues by severity
    if critical_issues:
        md += "\n## 🔴 Critical Issues\n\n"
        md += format_issues(critical_issues)
    
    if high_issues:
        md += "\n## ⚠️ High Priority\n\n"
        md += format_issues(high_issues)
    
    if medium_issues:
        md += "\n## 🟡 Medium Priority\n\n"
        md += format_issues(medium_issues)
    
    if low_issues:
        md += "\n## ℹ️ Low Priority\n\n"
        md += format_issues(low_issues)
    
    # Detailed findings
    md += "\n## Detailed Findings\n\n"
    md += format_detailed_findings(report)
    
    return md


def format_issues(issues: List[Dict]) -> str:
    """Format issues as Markdown list"""
    
    issue_icons = {
        "ai_agent_blocked": "🚫",
        "missing_llms_txt": "📄",
        "missing_agent_card": "🔧",
        "missing_jsonld": "🔍",
        "price_mismatch": "💰",
        "bilingual_inconsistency": "🌐",
        "poor_content_quality": "📝",
        "robotic_patterns": "🤖",
        "schema_validation_error": "⚠️"
    }
    
    output = ""
    for issue in issues:
        icon = issue_icons.get(issue.get("type"), "•")
        output += f"- {icon} **{issue.get('title')}**\n"
        output += f"  - {issue.get('description')}\n"
        if issue.get("recommendation"):
            output += f"  - *Fix:* {issue.get('recommendation')}\n"
        output += "\n"
    
    return output


def format_detailed_findings(report: Dict) -> str:
    """Generate detailed findings section"""
    
    findings = ""
    
    # Protocol compliance
    findings += "### Protocol Compliance\n\n"
    protocol = report.get("protocol", {})
    findings += f"- **llms.txt**: {protocol.get('llms_txt', {}).get('status', 'unknown')}\n"
    findings += f"- **agent-card.json**: {protocol.get('agent_card', {}).get('status', 'unknown')}\n"
    findings += f"- **robots.txt**: {protocol.get('robots_txt', {}).get('status', 'unknown')}\n\n"
    
    # Schema validation
    findings += "### Schema Validation\n\n"
    schema = report.get("schema", {})
    findings += f"- **Schema found**: {schema.get('schema_found', False)}\n"
    findings += f"- **Valid**: {schema.get('valid', False)}\n"
    if schema.get("errors"):
        findings += f"- **Errors**: {len(schema.get('errors', []))}\n"
    findings += "\n"
    
    # Edge visibility
    findings += "### AI Agent Accessibility\n\n"
    edge = report.get("edge_visibility", {})
    summary = edge.get("summary", {})
    findings += f"- **Total agents tested**: {summary.get('total_agents_tested', 0)}\n"
    findings += f"- **Accessible**: {summary.get('accessible_agents', 0)}\n"
    findings += f"- **Blocked**: {summary.get('blocked_agents', 0)}\n\n"
    
    # Content quality
    findings += "### Content Quality\n\n"
    content = report.get("content_quality", {})
    findings += f"- **Overall score**: {content.get('overall_score', 0)}/10\n"
    findings += f"- **Recommendation**: {content.get('recommendation', 'N/A')}\n\n"
    
    return findings
