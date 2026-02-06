"""
Test script for Crawl4AI Extractor

Run with: python test_crawler.py
"""

import asyncio
from app.services.crawler import extract_page_content, extract_bilingual_content


async def main():
    # Test URL
    test_url = "https://www.luxyhijab.com/ar/product/%d9%81%d8%b3%d8%aa%d8%a7%d9%86-%d8%a7%d8%b3%d9%88%d8%af-%d8%b7%d9%88%d9%8a%d9%84"
    
    print(f"Testing Crawl4AI extraction for: {test_url}\n")
    print("=" * 60)
    
    # Test basic extraction
    print("\n📄 Basic Content Extraction:")
    result = await extract_page_content(test_url)
    
    if result.get("success"):
        print(f"✅ Success!")
        print(f"  Platform: {result['platform']}")
        print(f"  Markdown length: {len(result['markdown'])} chars")
        print(f"  HTML length: {len(result['html'])} chars")
        print(f"  JSON-LD schemas found: {len(result['jsonld'])}")
        print(f"  Images extracted: {len(result['media']['images'])}")
        print(f"  Videos extracted: {len(result['media']['videos'])}")
        print(f"  Has screenshot: {result['screenshot'] is not None}")
        
        # Show first 500 chars of markdown
        print(f"\n📝 Markdown preview (first 500 chars):")
        print("-" * 60)
        print(result['markdown'][:500])
        print("-" * 60)
        print(result['jsonld'])
        """
        # Show JSON-LD if found
        if result['jsonld']:
            print(f"\n🔍 JSON-LD Schema Types:")
            for schema in result['jsonld']:
                schema_type = schema.get('@type', 'Unknown')
                print(f"  - {schema_type}")
                if schema_type == 'Product':
                    print(f"    Name: {schema.get('name', 'N/A')}")
                    print(f"    Price: {schema.get('offers', {}).get('price', 'N/A')}")
        
        # Show sample images
        if result['media']['images']:
            print(f"\n🖼️  Sample Images (first 3):")
            for img in result['media']['images'][:3]:
                print(f"  - {img.get('src', 'No src')[:80]}...")
    else:
        print(f"❌ Failed: {result.get('error')}")
        """
    """
    # Test bilingual extraction
    print("\n\n" + "=" * 60)
    print("\n🌐 Testing Bilingual Extraction:")
    bilingual_result = await extract_bilingual_content(test_url)

    print(f"\nArabic version:")
    ar = bilingual_result['arabic']
    if ar.get('success'):
        print(f"  ✅ Success - {len(ar['markdown'])} chars")
    else:
        print(f"  ❌ Failed: {ar.get('error')}")
    
    print(f"\nEnglish version:")
    en = bilingual_result['english']
    if en.get('success'):
        print(f"  ✅ Success - {len(en['markdown'])} chars")
    else:
        print(f"  ❌ Failed: {en.get('error')}")
    
    print("\n" + "=" * 60)
    **/**
"""

if __name__ == "__main__":
    asyncio.run(main())
