"""Test Content Scorer with URL Input

Tests the enhanced content scoring system with comprehensive Arabic quality validation.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler import extract_page_content
from app.services.content_scorer import score_product_content


async def test_content_scorer(url: str, ollama_host: str = "http://localhost:11434"):
    """
    Test content scorer with a product URL
    
    Args:
        url: Product page URL to analyze
        ollama_host: Ollama API endpoint
    """
    
    print(f"Testing Content Scorer for: {url}")
    print("=" * 80)
    print()
    
    # Extract page content
    print("� Extracting page content...")
    result = await extract_page_content(url)
    
    if not result.get('success'):
        print(f"❌ Failed to extract content: {result.get('error')}")
        return
    
    # Get extracted data
    text_content = result.get('markdown', '')[:2000]  # First 2000 chars
    html_content = result.get('html', '')
    jsonld_data = extract_jsonld(result.get('jsonld', []))
    
    print(f"✅ Content extracted")
    print(f"   Text length: {len(text_content)} chars")
    print(f"   Has HTML: {bool(html_content)}")
    print(f"   Has JSON-LD: {bool(jsonld_data)}")
    print()
    
    # Score the content
    print("🔍 Analyzing content quality...")
    print("-" * 80)
    
    score_result = await score_product_content(
        text=text_content,
        html=html_content,
        jsonld=jsonld_data,
        ollama_host=ollama_host,
        model="qwen3:8b"
    )
    
    # Display results
    print()
    print("=" * 80)
    print("📊 CONTENT QUALITY ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # Overall Score
    overall = score_result.get('overall_score', 0)
    severity = score_result.get('severity', 'unknown')
    
    print(f"🎯 Overall Score: {overall}/10")
    print(f"⚠️  Severity: {severity.upper()}")
    print(f"� Recommendation: {score_result.get('recommendation', 'N/A')}")
    print()
    
    # Score interpretation
    if overall >= 8:
        interpretation = "✨ EXCELLENT - Ready for AI agents"
    elif overall >= 6:
        interpretation = "✅ GOOD - Minor improvements needed"
    elif overall >= 4:
        interpretation = "⚠️  FAIR - Significant improvements needed"
    else:
        interpretation = "❌ POOR - Major rewrite required"
    
    print(f"📈 Interpretation: {interpretation}")
    print()
    
    # Detailed scores breakdown
    print("-" * 80)
    print("📋 DETAILED SCORES")
    print("-" * 80)
    print()
    
    # 1. Robotic Patterns
    robotic = score_result.get('robotic_patterns', {})
    print(f"1️⃣  Robotic Patterns: {robotic.get('score', 0)}/10")
    if robotic.get('issues'):
        print(f"   ⚠️  Issues found: {len(robotic['issues'])}")
        for issue in robotic['issues'][:3]:
            print(f"      - {issue.get('type')}: {issue.get('severity', 'unknown')} severity")
    else:
        print("   ✅ No robotic patterns detected")
    print()
    
    # 2. AEO Readiness
    aeo = score_result.get('aeo_readiness', {})
    print(f"2️⃣  AEO Readiness: {aeo.get('score', 0)}/10")
    if aeo.get('signals'):
        print(f"   ✅ Signals found: {', '.join(aeo['signals'])}")
    else:
        print("   ⚠️  No AEO signals detected")
    print()
    
    # 3. Structural Scannability (NEW)
    structural = score_result.get('structural_scannability', {})
    print(f"3️⃣  Structural Scannability (RTL): {structural.get('score', 0)}/10")
    print(f"   📍 Early price (first 100 chars): {'✅ Yes' if structural.get('has_early_price') else '❌ No'}")
    print(f"   📊 Spec tables: {'✅ Yes' if structural.get('has_tables') else '❌ No'}")
    print(f"   ❓ Question headers: {structural.get('question_headers_count', 0)}")
    if structural.get('issues'):
        for issue in structural['issues']:
            print(f"   ⚠️  {issue.get('message')}")
    print()
    
    # 4. Technical Authority (NEW)
    technical = score_result.get('technical_authority', {})
    print(f"4️⃣  Technical Authority: {technical.get('score', 0)}/10")
    local_signals = technical.get('local_trust_signals', [])
    if local_signals:
        print(f"   ✅ Local trust signals: {', '.join(local_signals[:3])}")
    else:
        print("   ⚠️  No local payment methods mentioned")
    
    missing_alt = technical.get('missing_alt_text_count', 0)
    if missing_alt > 0:
        print(f"   ⚠️  {missing_alt} images missing Arabic alt-text")
    
    if technical.get('issues'):
        for issue in technical['issues']:
            if issue.get('severity') == 'high':
                print(f"   ❌ {issue.get('message')}")
    print()
    
    # 5. LLM Analysis
    llm = score_result.get('llm_analysis', {})
    print(f"5️⃣  LLM Analysis:")
    
    if llm.get('skipped'):
        print(f"   ⏭️  Skipped: {llm.get('reasoning', 'N/A')}")
    else:
        print(f"   👤 Naturalness: {llm.get('naturalness', 0)}/10")
        print(f"   🔍 Keyword Stuffing (reverse): {llm.get('keyword_stuffing_reverse', 0)}/10")
        print(f"   🎯 AEO Readiness: {llm.get('aeo_readiness', 0)}/10")
        print(f"   🗣️  Dialect Usage: {llm.get('dialect_usage', 0)}/10")
        print(f"   📝 Linguistic Precision: {llm.get('linguistic_precision', 0)}/10")
        print(f"   🌐 Translation Quality: {llm.get('translation_quality', 0)}/10")
        
        if llm.get('local_terminology_used'):
            print(f"   ✅ Uses local terminology (e.g., جوال)")
        
        if llm.get('reasoning'):
            print(f"   💭 Analysis: {llm['reasoning']}")
    print()
    
    # Summary
    print("=" * 80)
    print("📌 SUMMARY")
    print("=" * 80)
    print()
    
    # Count issues
    total_issues = sum([
        len(robotic.get('issues', [])),
        len(structural.get('issues', [])),
        len(technical.get('issues', []))
    ])
    
    print(f"Total Issues Found: {total_issues}")
    print(f"Overall Quality: {overall}/10")
    print(f"Action Required: {score_result.get('recommendation', 'N/A')}")
    print()


def extract_jsonld(jsonld_list):
    """Extract product schema from JSON-LD list"""
    if not jsonld_list:
        return None
    
    for item in jsonld_list:
        if isinstance(item, dict) and item.get('@type') == 'Product':
            return item
    
    return None


if __name__ == "__main__":
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Default test URL (Arabic e-commerce)
        test_url = "https://www.luxyhijab.com/ar/product/%d9%81%d8%b3%d8%aa%d8%a7%d9%86-%d8%a7%d8%b3%d9%88%d8%af-%d8%b7%d9%88%d9%8a%d9%84"
    
    # Ollama host (can be customized)
    ollama_api = "http://localhost:11434"
    
    print()
    print("🚀 Content Scorer Test Script")
    print("=" * 80)
    print()
    
    # Run the test
    asyncio.run(test_content_scorer(test_url, ollama_api))
    
    print()
    print("✅ Test Complete!")
    print()
