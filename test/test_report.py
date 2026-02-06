"""
Test script for Report Generator

Run with: python test_report.py
Requires: All services running (Ollama, etc.)
"""

import asyncio
import json
from app.services.report_generator import generate_full_audit_report, generate_markdown_report


async def main():
    # Test URL
    test_url = "https://hijabti.ae/products/shimmer-georgette-hijab-dusty-rose"
    
    print("=" * 80)
    print("Testing Comprehensive AEO Audit Report Generator")
    print("=" * 80)
    print(f"\n📊 Generating full audit report for: {test_url}\n")
    print("This will run ALL services:")
    print("  1. Protocol Checker (llms.txt, agent-card.json, robots.txt)")
    print("  2. Content Extractor (bilingual)")
    print("  3. Schema Validator (JSON-LD Product)")
    print("  4. Edge Visibility Tester (AI agent blocking)")
    print("  5. Content Quality Scorer (Ollama)")
    print("\n" + "-" * 80)
    
    # Generate report
    report = await generate_full_audit_report(test_url)
    
    # Display summary
    print("\n\n📋 AUDIT SUMMARY")
    print("=" * 80)
    print(f"URL: {report['url']}")
    print(f"Overall Score: {report['overall_score']}/100")
    print(f"Severity: {report['severity'].upper()}")
    print(f"Total Issues: {len(report['issues'])}")
    
    # Group issues by severity
    issues_by_severity = {}
    for issue in report['issues']:
        severity = issue.get('severity', 'unknown')
        if severity not in issues_by_severity:
            issues_by_severity[severity] = []
        issues_by_severity[severity].append(issue)
    
    print(f"\nIssues Breakdown:")
    for severity in ['critical', 'high', 'medium', 'low']:
        count = len(issues_by_severity.get(severity, []))
        if count > 0:
            emoji = {'critical': '🔴', 'high': '⚠️', 'medium': '🟡', 'low': 'ℹ️'}
            print(f"  {emoji.get(severity, '•')} {severity.capitalize()}: {count}")
    
    # Display issues
    if report['issues']:
        print("\n\n🔍 DETECTED ISSUES")
        print("=" * 80)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = issues_by_severity.get(severity, [])
            if issues:
                emoji = {'critical': '🔴', 'high': '⚠️', 'medium': '🟡', 'low': 'ℹ️'}
                print(f"\n{emoji.get(severity, '•')} {severity.upper()} PRIORITY:")
                print("-" * 80)
                
                for issue in issues:
                    print(f"\n  • {issue.get('title')}")
                    print(f"    {issue.get('description')}")
                    if issue.get('recommendation'):
                        print(f"    💡 Fix: {issue.get('recommendation')}")
    
    # Display component scores
    print("\n\n📊 COMPONENT SCORES")
    print("=" * 80)
    
    # Protocol
    protocol = report.get('protocol', {})
    print(f"\n1. Protocol Compliance:")
    print(f"   • llms.txt: {protocol.get('llms_txt', {}).get('status', 'unknown')}")
    print(f"   • agent-card.json: {protocol.get('agent_card', {}).get('status', 'unknown')}")
    print(f"   • robots.txt: {protocol.get('robots_txt', {}).get('status', 'unknown')}")
    
    # Schema
    schema = report.get('schema', {})
    print(f"\n2. Schema Validation:")
    print(f"   • Schema found: {schema.get('schema_found', False)}")
    print(f"   • Valid: {schema.get('valid', False)}")
    if schema.get('errors'):
        print(f"   • Errors: {len(schema.get('errors', []))}")
    
    # Edge visibility
    edge = report.get('edge_visibility', {})
    summary = edge.get('summary', {})
    print(f"\n3. AI Agent Accessibility:")
    print(f"   • Total agents tested: {summary.get('total_agents_tested', 0)}")
    print(f"   • Accessible: {summary.get('accessible_agents', 0)} ✅")
    print(f"   • Blocked: {summary.get('blocked_agents', 0)} ❌")
    
    # Content quality
    content = report.get('content_quality', {})
    print(f"\n4. Content Quality:")
    print(f"   • Overall score: {content.get('overall_score', 0)}/10")
    print(f"   • Recommendation: {content.get('recommendation', 'N/A')}")
    
    # Bilingual
    bilingual = report.get('bilingual', {})
    if bilingual:
        print(f"\n5. Bilingual Consistency:")
        print(f"   • Consistent: {bilingual.get('consistent', False)}")
        if not bilingual.get('consistent'):
            print(f"   • Issues: {len(bilingual.get('issues', []))}")
    
    # Generate Markdown report
    print("\n\n📄 GENERATING MARKDOWN REPORT")
    print("=" * 80)
    
    markdown = generate_markdown_report(report)
    
    # Save to file
    filename = f"audit_report_{report['timestamp'].replace(':', '-').split('.')[0]}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Markdown report saved to: {filename}")
    
    # Save JSON report
    json_filename = filename.replace('.md', '.json')
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON report saved to: {json_filename}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
