"""
Test script for Content Scorer

Run with: python test_scorer.py
Requires: Ollama running with qwen3:8b model
"""

import asyncio
from app.services.content_scorer import score_product_content


async def main():
    # Test content samples
    print("=" * 80)
    print("Testing Human-First Content Scorer with Ollama qwen3:8b")
    print("=" * 80)
    
    # Test 1: Good human-like Arabic content
    print("\n\n📝 Test 1: Human-like Arabic Content")
    print("-" * 80)
    
    good_content = """فستان اسود طويل مناسب للمناسبات الرسمية
هذا الفستان مصنوع من قماش عالي الجودة ويتميز بتصميم أنيق وعصري. 
جربته في حفلة زواج وكان مريح جداً طول الليل.
ينفع للبنات اللي يحبون الأناقة البسيطة."""
    
    result1 = await score_product_content(good_content)
    display_results("Good Content", result1)
    
    # Test 2: Keyword-stuffed robotic content
    print("\n\n📝 Test 2: Keyword-Stuffed Robotic Content")
    print("-" * 80)
    
    bad_content = """فستان فستان فستان اسود طويل فستان فستان
احسن فستان في دبي احسن فستان في ابوظبي احسن فستان في الشارقة
BEST DRESS BEST DRESS BEST DRESS
فستان فستان فستان quality dress فستان فستان"""
    
    result2 = await score_product_content(bad_content)
    display_results("Keyword-Stuffed Content", result2)
    
    # Test 3: English content with Q&A structure
    print("\n\n📝 Test 3: English Content with Q&A Structure")
    print("-" * 80)
    
    english_content = """Black Long Dress for Formal Occasions

What is this dress made of?
This elegant black dress is crafted from premium quality fabric.

How to style it?
Perfect for weddings, parties, and formal events. Pair with heels for a sophisticated look.

Why choose this dress?
- Comfortable all-day wear
- Elegant and timeless design
- Suitable for various occasions"""
    
    result3 = await score_product_content(english_content)
    display_results("English Q&A Content", result3)
    
    print("\n" + "=" * 80)


def display_results(label: str, results: dict):
    """Display scoring results"""
    
    print(f"\n🎯 Results for: {label}")
    print(f"Overall Score: {results['overall_score']}/10")
    print(f"Severity: {results['severity'].upper()}")
    
    print(f"\n📊 Component Scores:")
    print(f"  Robotic Patterns: {results['robotic_patterns']['score']}/10")
    print(f"  AEO Readiness: {results['aeo_readiness']['score']}/10")
    
    llm = results['llm_analysis']
    if not llm.get('skipped'):
        print(f"\n🤖 LLM Analysis:")
        print(f"  Naturalness: {llm.get('naturalness', 'N/A')}/10")
        print(f"  Keyword Stuffing (Rev): {llm.get('keyword_stuffing_reverse', 'N/A')}/10")
        print(f"  AEO Readiness: {llm.get('aeo_readiness', 'N/A')}/10")
        print(f"  Dialect Usage: {llm.get('dialect_usage', 'N/A')}/10")
        print(f"  Reasoning: {llm.get('reasoning', 'N/A')}")
    else:
        print(f"\n⚠️  LLM Analysis: Skipped ({llm.get('reasoning', 'Unknown reason')})")
    
    # Robotic pattern issues
    if results['robotic_patterns']['has_issues']:
        print(f"\n⚠️  Robotic Pattern Issues:")
        for issue in results['robotic_patterns']['issues']:
            print(f"  - {issue['type']} (severity: {issue['severity']})")
    
    # AEO signals
    if results['aeo_readiness']['signals']:
        print(f"\n✅ AEO Signals Found:")
        for signal in results['aeo_readiness']['signals']:
            print(f"  - {signal}")
    
    print(f"\n💡 Recommendation:")
    print(f"  {results['recommendation']}")


if __name__ == "__main__":
    print("\n⚙️  Make sure Ollama is running with qwen3:8b model:")
    print("   $ ollama serve")
    print("   $ ollama pull qwen3:8b\n")
    
    asyncio.run(main())
