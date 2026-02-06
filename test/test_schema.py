"""
Test script for JSON-LD Schema Validator

Run with: python test_schema.py
"""

import asyncio
from app.services.crawler import extract_page_content, extract_bilingual_content
from app.services.schema_validator import (
    validate_product_schema,
    verify_metadata_language,
    compare_visible_vs_structured,
    validate_bilingual_schemas,
    find_product_schema
)


async def main():
    # Test URL
    test_url = "https://www.luxyhijab.com/ar/product/%d9%81%d8%b3%d8%aa%d8%a7%d9%86-%d8%a7%d8%b3%d9%88%d8%af-%d8%b7%d9%88%d9%8a%d9%84"
    
    print(f"Testing JSON-LD validation for: {test_url}\n")
    print("=" * 60)
    
    # Extract page content
    print("\n📄 Extracting page content...")
    result = await extract_page_content(test_url)
    
    if not result.get("success"):
        print(f"❌ Failed to extract content: {result.get('error')}")
        return
    
    print(f"✅ Extracted {len(result['jsonld'])} JSON-LD blocks")
    
    # Validate Product schema
    print("\n🔍 Validating Product Schema:")
    print("-" * 60)
    
    validation = validate_product_schema(result['jsonld'])
    
    print(f"Schema Found: {validation['found']}")
    print(f"Valid: {validation['valid']}")
    print(f"Severity: {validation['severity']}")
    
    # UCP Compliance Metrics
    print(f"\n🎯 UCP Readiness Score: {validation.get('ucp_readiness_score', 0)}%")
    print(f"UCP Compliant: {'✅ Yes' if validation.get('ucp_compliant') else '❌ No'}")
    
    # Score interpretation
    score = validation.get('ucp_readiness_score', 0)
    if score >= 90:
        interpretation = "Excellent - Fully UCP compliant"
    elif score >= 70:
        interpretation = "Good - Most UCP requirements met"
    elif score >= 50:
        interpretation = "Fair - Basic compliance, missing key signals"
    else:
        interpretation = "Poor - Major UCP gaps"
    print(f"Score Interpretation: {interpretation}")
    
    if validation['errors']:
        print(f"\n❌ Errors ({len(validation['errors'])}):")
        for error in validation['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ No errors")
    
    if validation['warnings']:
        print(f"\n⚠️  Warnings ({len(validation['warnings'])}):")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if validation.get('ucp_missing'):
        print(f"\n📊 Missing UCP Fields ({len(validation['ucp_missing'])}):")
        for missing in validation['ucp_missing']:
            print(f"  - {missing}")
    
    if validation.get('product_data'):
        pd = validation['product_data']
        print(f"\n📦 Product Data:")
        print(f"  Name: {pd['name']}")
        print(f"  Price: {pd['price']} {pd['currency']}")
        print(f"  Availability: {pd['availability']}")
    
    # Test visible vs structured comparison
    print("\n\n📊 Comparing Visible vs Structured Data:")
    print("-" * 60)
    
    product_schema = find_product_schema(result['jsonld'])
    if product_schema:
        comparison = compare_visible_vs_structured(result['markdown'], product_schema)
        
        print(f"Matches: {comparison['matches']}")
        print(f"Severity: {comparison['severity']}")
        
        if comparison['mismatches']:
            print(f"\n❌ Mismatches found:")
            for mismatch in comparison['mismatches']:
                print(f"  Field: {mismatch['field']}")
                print(f"  Severity: {mismatch['severity']}")
                print(f"  Issue: {mismatch['issue']}")
                if 'structured_value' in mismatch:
                    print(f"  Structured: {mismatch['structured_value']}")
                if 'visible_values' in mismatch:
                    print(f"  Visible: {mismatch['visible_values']}")
                print()
        else:
            print("✅ No mismatches - data is consistent")
    
    # Test bilingual validation
    print("\n\n🌐 Testing Bilingual Schema Consistency:")
    print("-" * 60)
    
    bilingual = await extract_bilingual_content(test_url)
    
    if bilingual['arabic'].get('success') and bilingual['english'].get('success'):
        ar_jsonld = bilingual['arabic']['jsonld']
        en_jsonld = bilingual['english']['jsonld']
        
        bilingual_validation = validate_bilingual_schemas(ar_jsonld, en_jsonld)
        
        print(f"Consistent: {bilingual_validation['consistent']}")
        print(f"Severity: {bilingual_validation['severity']}")
        
        if bilingual_validation['issues']:
            print(f"\n❌ Issues found:")
            for issue in bilingual_validation['issues']:
                print(f"  [{issue['severity'].upper()}] {issue['issue']}")
        else:
            print("✅ Both language versions have consistent schemas")
    else:
        print("❌ Could not extract bilingual content")
        if not bilingual['arabic'].get('success'):
            print(f"  Arabic: {bilingual['arabic'].get('error')}")
        if not bilingual['english'].get('success'):
            print(f"  English: {bilingual['english'].get('error')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
