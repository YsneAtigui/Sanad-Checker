"""Quick test for UCP validator"""
import json
from app.services.schema_validator import validate_product_schema

# Test with a basic Product schema
test_schema = {
    "@context": "https://schema.org/",
    "@type": "Product",
    "@id": "https://example.com/product#product",
    "name": "Test Product",
    "description": "This is a test product with a description that has more than fifty words to meet the UCP requirement for AI-friendly content that is fact-dense and optimized for citations by AI agents and answer engines in 2026.",
    "sku": "TEST-123",
    "image": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
    "brand": {
        "@type": "Brand",
        "name": "Test Brand",
        "sameAs": ["https://instagram.com/testbrand"]
    },
    "gtin13": "1234567890123",
    "offers": {
        "@type": "Offer",
        "url": "https://example.com/product",
        "price": "299.00",
        "priceCurrency": "SAR",
        "priceValidUntil": "2026-12-31",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "hasMerchantReturnPolicy": {
            "@type": "MerchantReturnPolicy",
            "applicableCountry": "SA",
            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
            "merchantReturnDays": 14,
            "returnMethod": "https://schema.org/ReturnByMail",
            "returnFees": "https://schema.org/FreeReturn",
            "merchantReturnLink": "https://example.com/returns"
        },
        "shippingDetails": {
            "@type": "OfferShippingDetails",
            "shippingRate": {
                "@type": "MonetaryAmount",
                "value": "0.00",
                "currency": "SAR"
            },
            "deliveryTime": {
                "@type": "ShippingDeliveryTime",
                "handlingTime": {
                    "@type": "QuantitativeValue",
                    "minValue": 0,
                    "maxValue": 1,
                    "unitCode": "d"
                },
                "transitTime": {
                    "@type": "QuantitativeValue",
                    "minValue": 1,
                    "maxValue": 3,
                    "unitCode": "d"
                }
            }
        }
    },
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.8",
        "reviewCount": "124"
    }
}

print("Testing UCP-Compliant JSON-LD Validator")
print("=" * 60)

validation = validate_product_schema([test_schema])

print(f"\n✅ Schema Found: {validation['found']}")
print(f"✅ Valid: {validation['valid']}")
print(f"🎯 UCP Readiness Score: {validation['ucp_readiness_score']}%")
print(f"✅ UCP Compliant: {validation['ucp_compliant']}")

print(f"\n📊 Results:")
print(f"  Errors: {len(validation['errors'])}")
print(f"  Warnings: {len(validation['warnings'])}")
print(f"  UCP Missing: {len(validation['ucp_missing'])}")

if validation['errors']:
    print(f"\n❌ Errors:")
    for error in validation['errors']:
        print(f"  - {error}")

if validation['warnings']:
    print(f"\n⚠️  Warnings:")
    for warning in validation['warnings']:
        print(f"  - {warning}")

if validation['ucp_missing']:
    print(f"\n📋 Missing UCP Fields:")
    for missing in validation['ucp_missing']:
        print(f"  - {missing}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
