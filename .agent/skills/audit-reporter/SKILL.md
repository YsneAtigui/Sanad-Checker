---
name: audit-reporter
description: Generate comprehensive AEO audit reports with severity-based prioritization. Create structured reports showing protocol compliance, visibility issues, and actionable recommendations for Arabic e-commerce sites. Use when finalizing audits or presenting findings to users.
---

# AEO Audit Reporter

Generate comprehensive, prioritized audit reports for Sanad AEO audits.

## Report Structure

```markdown
# AEO Audit Report: [Store Name]

**URL:** [url]
**Platform:** [Salla/Zid/Shopify]
**Audit Date:** [timestamp]
**Overall Score:** [0-100]

## Executive Summary

[1-2 paragraph overview of key findings]

## Critical Issues 🔴

[Issues that block AI agent visibility]

## High Priority ⚠️

[Issues that significantly reduce visibility]

## Medium Priority 🟡

[Recommendations for improvement]

## Low Priority ℹ️

[Nice-to-have optimizations]

## Detailed Findings

### Protocol Compliance
[llms.txt, agent-card.json, robots.txt results]

### Schema Validation
[JSON-LD findings]

### Content Quality
[Human-first scoring results]

### Bilingual Consistency
[Arabic/English symmetry]

## Recommendations

[Prioritized action items]
```

## Severity Classification

```python
def classify_severity(issue: dict) -> str:
    """
    Classify issue severity based on visibility impact
    """
    
    critical_conditions = [
        issue.get("type") == "ai_agent_blocked",
        issue.get("type") == "cloudflare_block",
        issue.get("type") == "price_mismatch",
        issue.get("field") == "price" and issue.get("mismatched"),
    ]
    
    high_conditions = [
        issue.get("type") == "missing_llms_txt",
        issue.get("type") == "missing_jsonld",
        issue.get("type") == "hreflang_broken",
        issue.get("score", 10) < 3,  # Content score
    ]
    
    medium_conditions = [
        issue.get("type") == "missing_agent_card",
        issue.get("type") == "metadata_language_mismatch",
        issue.get("score", 10) < 6,
    ]
    
    if any(critical_conditions):
        return "critical"
    elif any(high_conditions):
        return "high"
    elif any(medium_conditions):
        return "medium"
    else:
        return "low"
```

## Score Calculation

```python
def calculate_overall_score(audit_results: dict) -> int:
    """
    Calculate 0-100 AEO score
    """
    
    weights = {
        "protocol": 30,      # llms.txt, agent-card, robots.txt
        "schema": 25,        # JSON-LD validity
        "content": 20,       # Human-first score
        "bilingual": 15,     # Hreflang + language consistency
        "accessibility": 10  # AI agent access (not blocked)
    }
    
    scores = {}
    
    # Protocol score
    protocol_checks = 0
    protocol_passed = 0
    for check in ["llms_txt", "agent_card", "robots_txt"]:
        protocol_checks += 1
        if audit_results["protocol"].get(check, {}).get("status") in ["found", "valid"]:
            protocol_passed += 1
    scores["protocol"] = (protocol_passed / protocol_checks) * 100
    
    # Schema score
    scores["schema"] = 100 if audit_results["schema"].get("valid") else 0
    
    # Content score (already 0-10, scale to 100)
    scores["content"] = audit_results["content"].get("overall_score", 0) * 10
    
    # Bilingual score
    bilingual_score = 100
    if not audit_results["bilingual"].get("symmetric"):
        bilingual_score -= 40
    if not audit_results["bilingual"].get("language_match"):
        bilingual_score -= 60
    scores["bilingual"] = max(0, bilingual_score)
    
    # Accessibility score
    scores["accessibility"] = 0 if audit_results["access"].get("blocked") else 100
    
    # Weighted average
    overall = sum(scores[k] * (weights[k] / 100) for k in weights)
    
    return round(overall)
```

## Report Generation

```python
def generate_audit_report(audit_results: dict, store_info: dict) -> str:
    """
    Generate complete Markdown report
    """
    
    overall_score = calculate_overall_score(audit_results)
    
    # Collect and classify all issues
    issues = collect_issues(audit_results)
    classified = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }
    
    for issue in issues:
        severity = classify_severity(issue)
        classified[severity].append(issue)
    
    # Generate report sections
    report = f"""# AEO Audit Report: {store_info['name']}

**URL:** {store_info['url']}
**Platform:** {store_info.get('platform', 'Unknown')}
**Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Overall Score:** {overall_score}/100 {get_score_emoji(overall_score)}

## Executive Summary

{generate_executive_summary(overall_score, classified)}

"""
    
    # Add issue sections
    if classified["critical"]:
        report += "\n## 🔴 Critical Issues\n\n"
        report += format_issues(classified["critical"])
    
    if classified["high"]:
        report += "\n## ⚠️ High Priority\n\n"
        report += format_issues(classified["high"])
    
    if classified["medium"]:
        report += "\n## 🟡 Medium Priority\n\n"
        report += format_issues(classified["medium"])
    
    if classified["low"]:
        report += "\n## ℹ️ Low Priority\n\n"
        report += format_issues(classified["low"])
    
    # Detailed findings
    report += "\n## Detailed Findings\n\n"
    report += generate_detailed_findings(audit_results)
    
    # Recommendations
    report += "\n## Recommended Actions\n\n"
    report += generate_recommendations(classified)
    
    return report

def get_score_emoji(score: int) -> str:
    if score >= 80:
        return "✅"
    elif score >= 60:
        return "⚠️"
    else:
        return "🔴"

def generate_executive_summary(score: int, issues: dict) -> str:
    """Generate 1-2 paragraph summary"""
    
    critical_count = len(issues["critical"])
    high_count = len(issues["high"])
    
    if critical_count > 0:
        return f"""This site has **{critical_count} critical issue(s)** blocking AI agent visibility. Immediate action required to enable Answer Engine indexing.

Overall AEO score: {score}/100. Priority should be given to resolving critical blockers before optimizing other aspects."""
    
    elif score >= 80:
        return f"""This site is well-optimized for Answer Engine visibility with a score of {score}/100. Minor improvements recommended.

No critical issues detected. The site follows AEO best practices and is accessible to major AI agents."""
    
    else:
        return f"""This site requires optimization for Answer Engine visibility (score: {score}/100). {high_count} high-priority issue(s) detected.

While not critically blocked, significant improvements are needed to maximize AI agent discoverability."""

def format_issues(issues: list) -> str:
    """Format issues as Markdown list"""
    
    output = ""
    for issue in issues:
        icon = get_issue_icon(issue["type"])
        output += f"- {icon} **{issue['title']}**\n"
        output += f"  - {issue['description']}\n"
        if "recommendation" in issue:
            output += f"  - *Fix:* {issue['recommendation']}\n"
        output += "\n"
    
    return output

def get_issue_icon(issue_type: str) -> str:
    icons = {
        "ai_agent_blocked": "🚫",
        "missing_llms_txt": "📄",
        "missing_jsonld": "🔍",
        "price_mismatch": "💰",
        "hreflang_broken": "🌐",
        "keyword_stuffing": "📝",
    }
    return icons.get(issue_type, "•")
```

## Detailed Findings Sections

```python
def generate_detailed_findings(audit_results: dict) -> str:
    """Generate detailed findings section"""
    
    findings = ""
    
    # Protocol compliance
    findings += "### Protocol Compliance\n\n"
    findings += format_protocol_findings(audit_results["protocol"])
    
    # Schema validation
    findings += "\n### Schema Validation\n\n"
    findings += format_schema_findings(audit_results["schema"])
    
    # Content quality
    findings += "\n### Content Quality\n\n"
    findings += format_content_findings(audit_results["content"])
    
    # Bilingual consistency (if applicable)
    if audit_results.get("bilingual"):
        findings += "\n### Bilingual Consistency\n\n"
        findings += format_bilingual_findings(audit_results["bilingual"])
    
    return findings
```

## Export Formats

Support multiple output formats:

```python
def export_report(audit_results: dict, format: str = "markdown"):
    """
    Export report in different formats
    """
    
    if format == "markdown":
        return generate_audit_report(audit_results, store_info)
    
    elif format == "json":
        return json.dumps({
            "score": calculate_overall_score(audit_results),
            "timestamp": datetime.now().isoformat(),
            "results": audit_results
        }, ensure_ascii=False, indent=2)
    
    elif format == "html":
        # Convert Markdown to HTML
        import markdown
        md_report = generate_audit_report(audit_results, store_info)
        return markdown.markdown(md_report)
```

## Critical Rules

- Always prioritize issues by severity (critical → low)
- Include actionable recommendations for each issue
- Use emojis/icons for visual clarity
- Score should reflect actual AI agent visibility impact
- Executive summary must be concise (2 paragraphs max)
- For Arabic reports, ensure proper RTL text rendering
