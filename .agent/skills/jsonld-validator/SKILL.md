---
name: jsonld-validator
description: Validate JSON-LD structured data for 2026-ready e-commerce Product schema with UCP (Universal Commerce Protocol) compliance. Check price, currency, availability, ratings, return policy, shipping details, GTIN-13, brand authority, and bilingual hreflang symmetry. Use when auditing product pages for Agentic Commerce readiness, detecting schema errors, or verifying Arabic/English metadata consistency.
---

# JSON-LD Validator

Validate comprehensive 2026-ready e-commerce Product schema for Agentic Commerce and Universal Commerce Protocol (UCP) compliance, ensuring full bilingual consistency for AEO.

## 2026-Ready Product Schema Validation

### Master Template Reference

The perfect JSON-LD structure for Agentic Commerce includes:

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "@id": "https://yourstore.com/products/premium-item#product",
  "name": "Product Name",
  "image": [
    "https://yourstore.com/images/prod-1.jpg",
    "https://yourstore.com/images/prod-2.jpg"
  ],
  "description": "A 50-word, fact-dense summary optimized for AI citations and human clarity.",
  "sku": "UNIQUE-SKU-123",
  "gtin13": "1234567890123", 
  "brand": {
    "@type": "Brand",
    "name": "Your Brand Name",
    "sameAs": [
      "https://instagram.com/yourbrand",
      "https://tiktok.com/@yourbrand"
    ]
  },
  "offers": {
    "@type": "Offer",
    "url": "https://yourstore.com/products/premium-item",
    "priceCurrency": "SAR",
    "price": "299.00",
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
      "merchantReturnLink": "https://yourstore.com/policies/refund-policy"
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
```

### Required Fields (CRITICAL)

```python
REQUIRED_FIELDS = [
    "@context": "https://schema.org/",
    "@type": "Product",
    "@id",  # Unique canonical URL with fragment
    "name",
    "description",  # 50+ words, fact-dense for AI citations
    "sku",
    "image",  # Array of images recommended
    "offers": {
        "@type": "Offer",
        "url",
        "price",
        "priceCurrency",  # SAR, AED, KWD, BHD, OMR, QAR
        "priceValidUntil",  # YYYY-MM-DD format
        "availability",  # Full schema.org URL format
        "itemCondition"  # https://schema.org/NewCondition or similar
    }
]

HIGHLY_RECOMMENDED_UCP_FIELDS = [
    "gtin13",  # GTIN-13 barcode for product authority
    "brand": {
        "@type": "Brand",
        "name",
        "sameAs"  # Array of social media URLs (Instagram, TikTok, etc.)
    },
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue",
        "reviewCount"
    },
    "offers.hasMerchantReturnPolicy": {
        "@type": "MerchantReturnPolicy",
        "applicableCountry",  # SA, AE, KW, BH, OM, QA
        "returnPolicyCategory",  # schema.org URL
        "merchantReturnDays",
        "returnMethod",
        "returnFees",
        "merchantReturnLink"  # Link to actual policy page
    },
    "offers.shippingDetails": {
        "@type": "OfferShippingDetails",
        "shippingRate": {
            "@type": "MonetaryAmount",
            "value",
            "currency"
        },
        "deliveryTime": {
            "@type": "ShippingDeliveryTime",
            "handlingTime": {
                "@type": "QuantitativeValue",
                "minValue",
                "maxValue",
                "unitCode": "d"  # days
            },
            "transitTime": {
                "@type": "QuantitativeValue",
                "minValue",
                "maxValue",
                "unitCode": "d"
            }
        }
    }
]
```

### Comprehensive UCP Validation Function

```python
def validate_product_jsonld(jsonld: dict) -> dict:
    """
    Validate Product JSON-LD schema for 2026 UCP compliance
    Returns detailed errors, warnings, and UCP readiness score
    """
    errors = []
    warnings = []
    ucp_missing = []  # Highly recommended UCP fields
    
    # === CRITICAL REQUIRED FIELDS ===
    
    # Check @context
    if jsonld.get("@context") != "https://schema.org/":
        errors.append("Missing or incorrect '@context'. Must be 'https://schema.org/'")
    
    # Check @type
    if jsonld.get("@type") != "Product":
        errors.append("@type must be 'Product'")
    
    # Check @id (unique canonical URL)
    if not jsonld.get("@id"):
        errors.append("Missing '@id' - unique canonical product URL required for UCP")
    elif "#product" not in jsonld["@id"]:
        warnings.append("@id should include fragment identifier (e.g., #product)")
    
    # Check name
    if not jsonld.get("name"):
        errors.append("Missing 'name' field")
    
    # Check description (50+ words recommended)
    description = jsonld.get("description", "")
    if not description:
        errors.append("Missing 'description' - required for AI citations")
    elif len(description.split()) < 50:
        warnings.append(f"Description too short ({len(description.split())} words). Aim for 50+ words for AI-friendly content")
    
    # Check SKU
    if not jsonld.get("sku"):
        errors.append("Missing 'sku' field")
    
    # Check image (array recommended)
    images = jsonld.get("image")
    if not images:
        errors.append("Missing 'image' field")
    elif isinstance(images, str):
        warnings.append("'image' should be an array of multiple product images")
    elif isinstance(images, list) and len(images) < 2:
        warnings.append("Only 1 image provided. Multiple images recommended for better visibility")
    
    # === VALIDATE OFFERS ===
    offers = jsonld.get("offers", {})
    if not isinstance(offers, dict):
        offers = offers[0] if isinstance(offers, list) else {}
    
    # Check Offer @type
    if offers.get("@type") != "Offer":
        warnings.append("offers.@type should be 'Offer'")
    
    # Check offer URL
    if not offers.get("url"):
        errors.append("Missing 'offers.url'")
    
    # Check price
    if not offers.get("price"):
        errors.append("Missing 'offers.price'")
    
    # Check priceCurrency
    if not offers.get("priceCurrency"):
        errors.append("Missing 'offers.priceCurrency'")
    elif offers["priceCurrency"] not in ["SAR", "AED", "KWD", "BHD", "OMR", "QAR"]:
        warnings.append(f"Non-Middle East currency: {offers['priceCurrency']}")
    
    # Check priceValidUntil
    if not offers.get("priceValidUntil"):
        errors.append("Missing 'offers.priceValidUntil' (YYYY-MM-DD format)")
    else:
        # Validate date format
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', offers["priceValidUntil"]):
            errors.append("'priceValidUntil' must be in YYYY-MM-DD format")
    
    # Validate availability (must use full schema.org URL)
    valid_availability = [
        "https://schema.org/InStock",
        "https://schema.org/OutOfStock",
        "https://schema.org/PreOrder",
        "https://schema.org/SoldOut",
        "https://schema.org/LimitedAvailability"
    ]
    availability = offers.get("availability", "")
    if not availability:
        errors.append("Missing 'offers.availability'")
    elif availability not in valid_availability:
        if availability in ["InStock", "OutOfStock", "PreOrder"]:
            errors.append(f"Use full schema.org URL for availability: 'https://schema.org/{availability}'")
        else:
            errors.append(f"Invalid availability: {availability}")
    
    # Check itemCondition
    if not offers.get("itemCondition"):
        warnings.append("Missing 'offers.itemCondition' - specify NewCondition, UsedCondition, etc.")
    
    # === UCP HIGHLY RECOMMENDED FIELDS ===
    
    # Check GTIN-13
    if not jsonld.get("gtin13"):
        ucp_missing.append("gtin13 - GTIN-13 barcode increases product authority and trust")
    else:
        # Validate GTIN-13 length
        gtin = str(jsonld["gtin13"])
        if len(gtin) != 13:
            errors.append(f"Invalid gtin13 length: {len(gtin)}. Must be exactly 13 digits")
    
    # Check brand with social media
    brand = jsonld.get("brand", {})
    if not brand:
        ucp_missing.append("brand - Brand information increases authority")
    else:
        if brand.get("@type") != "Brand":
            warnings.append("brand.@type should be 'Brand'")
        if not brand.get("name"):
            errors.append("Missing 'brand.name'")
        
        # Check for social media links (sameAs)
        same_as = brand.get("sameAs", [])
        if not same_as:
            ucp_missing.append("brand.sameAs - Social media links (Instagram, TikTok) boost brand authority")
        elif not isinstance(same_as, list):
            warnings.append("brand.sameAs should be an array of URLs")
    
    # Check aggregateRating
    rating = jsonld.get("aggregateRating")
    if not rating:
        ucp_missing.append("aggregateRating - Reviews and ratings significantly improve AI visibility")
    else:
        if rating.get("@type") != "AggregateRating":
            warnings.append("aggregateRating.@type should be 'AggregateRating'")
        if not rating.get("ratingValue"):
            errors.append("Missing 'aggregateRating.ratingValue'")
        if not rating.get("reviewCount"):
            errors.append("Missing 'aggregateRating.reviewCount'")
    
    # === CHECK MERCHANT RETURN POLICY ===
    return_policy = offers.get("hasMerchantReturnPolicy", {})
    if not return_policy:
        ucp_missing.append("hasMerchantReturnPolicy - Return policy is critical for e-commerce trust signals")
    else:
        if return_policy.get("@type") != "MerchantReturnPolicy":
            warnings.append("hasMerchantReturnPolicy.@type should be 'MerchantReturnPolicy'")
        
        # Check required return policy fields
        if not return_policy.get("applicableCountry"):
            errors.append("Missing 'hasMerchantReturnPolicy.applicableCountry'")
        
        if not return_policy.get("returnPolicyCategory"):
            errors.append("Missing 'hasMerchantReturnPolicy.returnPolicyCategory'")
        
        if not return_policy.get("merchantReturnDays"):
            warnings.append("Missing 'merchantReturnDays' - specify return window")
        
        if not return_policy.get("returnMethod"):
            warnings.append("Missing 'returnMethod' (e.g., ReturnByMail)")
        
        if not return_policy.get("returnFees"):
            warnings.append("Missing 'returnFees' (e.g., FreeReturn)")
        
        if not return_policy.get("merchantReturnLink"):
            warnings.append("Missing 'merchantReturnLink' - link to full return policy page")
    
    # === CHECK SHIPPING DETAILS ===
    shipping = offers.get("shippingDetails", {})
    if not shipping:
        ucp_missing.append("shippingDetails - Shipping information is essential for e-commerce AI agents")
    else:
        if shipping.get("@type") != "OfferShippingDetails":
            warnings.append("shippingDetails.@type should be 'OfferShippingDetails'")
        
        # Check shipping rate
        shipping_rate = shipping.get("shippingRate", {})
        if not shipping_rate:
            warnings.append("Missing 'shippingDetails.shippingRate'")
        else:
            if not shipping_rate.get("value"):
                warnings.append("Missing 'shippingRate.value'")
            if not shipping_rate.get("currency"):
                warnings.append("Missing 'shippingRate.currency'")
        
        # Check delivery time
        delivery_time = shipping.get("deliveryTime", {})
        if not delivery_time:
            warnings.append("Missing 'shippingDetails.deliveryTime'")
        else:
            # Check handling time
            handling = delivery_time.get("handlingTime", {})
            if not handling:
                warnings.append("Missing 'deliveryTime.handlingTime'")
            
            # Check transit time
            transit = delivery_time.get("transitTime", {})
            if not transit:
                warnings.append("Missing 'deliveryTime.transitTime'")
    
    # === CALCULATE UCP READINESS SCORE ===
    total_checks = 8  # GTIN, brand, rating, return policy, shipping, etc.
    ucp_score = ((total_checks - len(ucp_missing)) / total_checks) * 100
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "ucp_missing": ucp_missing,
        "ucp_readiness_score": round(ucp_score, 1),
        "ucp_compliant": len(errors) == 0 and len(ucp_missing) == 0
    }
```

## Hreflang Symmetry Check

Verify bidirectional language linking:

```python
def check_hreflang_symmetry(ar_page_url: str, en_page_url: str):
    """
    Verify that:
    1. Arabic page links to English via hreflang
    2. English page links to Arabic via hreflang
    3. Each page has self-referencing hreflang
    """
    
    # Extract hreflang tags from both pages
    ar_hreflangs = extract_hreflang_tags(ar_page_url)
    en_hreflangs = extract_hreflang_tags(en_page_url)
    
    issues = []
    
    # Check AR page links to EN
    if en_page_url not in ar_hreflangs.get("en", ""):
        issues.append("Arabic page missing hreflang to English version")
    
    # Check EN page links to AR
    if ar_page_url not in en_hreflangs.get("ar", ""):
        issues.append("English page missing hreflang to Arabic version")
    
    # Check self-reference
    if ar_page_url not in ar_hreflangs.get("ar", ""):
        issues.append("Arabic page missing self-referencing hreflang")
    
    return {
        "symmetric": len(issues) == 0,
        "issues": issues
    }
```

## Metadata Language Verification

Ensure Arabic pages actually use Arabic metadata:

```python
def verify_metadata_language(page_lang: str, jsonld: dict):
    """
    Check if metadata language matches page language
    """
    import re
    
    # Extract text from JSON-LD
    name = jsonld.get("name", "")
    description = jsonld.get("description", "")
    
    # Simple Arabic character detection
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    has_arabic = bool(arabic_pattern.search(name + description))
    
    if page_lang == "ar" and not has_arabic:
        return {
            "valid": False,
            "issue": "Arabic page has non-Arabic metadata",
            "severity": "high"
        }
    
    return {"valid": True}
```

## Data-Visible Content Matching

Prevent "hallucination risk" by comparing visible content with JSON-LD:

```python
def compare_visible_vs_structured(visible_text: str, jsonld: dict):
    """
    Compare visible page content with JSON-LD data
    Focus on: price, product name, availability
    """
    from arabic_normalizer import normalize_arabic, extract_arabic_numbers
    
    mismatches = []
    
    # Price comparison
    visible_price = extract_arabic_numbers(visible_text)
    jsonld_price = float(jsonld.get("offers", {}).get("price", 0))
    
    if abs(visible_price - jsonld_price) > 0.01:
        mismatches.append({
            "field": "price",
            "visible": visible_price,
            "structured": jsonld_price,
            "severity": "critical"
        })
    
    # Product name comparison (basic)
    normalized_visible = normalize_arabic(visible_text)
    normalized_name = normalize_arabic(jsonld.get("name", ""))
    
    if normalized_name not in normalized_visible:
        mismatches.append({
            "field": "name",
            "issue": "Product name not found in visible content",
            "severity": "medium"
        })
    
    return {
        "matches": len(mismatches) == 0,
        "mismatches": mismatches
    }
```

## Multiple JSON-LD Blocks

Handle pages with multiple JSON-LD scripts:

```python
def extract_all_jsonld(html_content: str) -> list:
    """Extract all JSON-LD blocks from HTML"""
    import json
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all('script', type='application/ld+json')
    
    jsonld_blocks = []
    for script in scripts:
        try:
            data = json.loads(script.string)
            jsonld_blocks.append(data)
        except json.JSONDecodeError:
            pass
    
    # Find Product schema
    product_schema = None
    for block in jsonld_blocks:
        if block.get("@type") == "Product":
            product_schema = block
            break
        # Handle @graph arrays
        if "@graph" in block:
            for item in block["@graph"]:
                if item.get("@type") == "Product":
                    product_schema = item
                    break
    
    return product_schema
```

## Output Format

The comprehensive validation returns:

```python
{
    "valid": bool,  # No critical errors
    "errors": [...],  # Critical compliance failures
    "warnings": [...],  # Non-critical issues
    "ucp_missing": [...],  # Missing UCP-recommended fields
    "ucp_readiness_score": float,  # 0-100 score
    "ucp_compliant": bool,  # True if fully UCP compliant
    "hreflang_symmetric": bool,
    "metadata_language_match": bool,
    "visible_vs_structured": {
        "matches": bool,
        "mismatches": [...]
    }
}
```

### Severity Levels

- **CRITICAL** (errors): Missing required fields, invalid formats, price mismatches
- **HIGH** (warnings): Missing recommended fields, format improvements needed
- **MEDIUM** (ucp_missing): UCP fields that boost AI visibility and trust

### UCP Readiness Scoring

The UCP readiness score is calculated based on presence of:
1. **GTIN-13** (barcode for product authority)
2. **Brand with social media** (brand authority signals)
3. **Aggregate rating** (trust and visibility)
4. **Merchant return policy** (complete with all fields)
5. **Shipping details** (delivery and cost transparency)
6. **Multiple images** (visual richness)
7. **Rich description** (50+ words for AI citations)
8. **Item condition** (product state clarity)

**Score = (fields_present / 8) × 100**

- **90-100%**: "Excellent - Fully UCP compliant"
- **70-89%**: "Good - Most UCP requirements met"
- **50-69%**: "Fair - Basic compliance, missing key signals"
- **<50%**: "Poor - Major UCP gaps"

## Critical Rules

### For 2026 UCP Compliance:

1. **Use Full Schema.org URLs**: 
   - ✅ `"availability": "https://schema.org/InStock"`
   - ❌ `"availability": "InStock"`

2. **Require @id with Fragment**:
   - ✅ `"@id": "https://store.com/product#product"`
   - ⚠️ `"@id": "https://store.com/product"` (missing fragment)

3. **Validate priceCurrency** for Middle East:
   - Valid: SAR, AED, KWD, BHD, OMR, QAR
   - Warn for other currencies

4. **Check Offer Arrays**:
   - Handle both single offers and offer arrays
   - Validate each offer independently

5. **Normalize Arabic Text**:
   - Always use `arabic-normalizer` skill before comparison
   - Handle character variants (ي vs ى)

6. **Flag Price Mismatches as CRITICAL**:
   - Compare visible vs structured data
   - Allow ±0.01 tolerance for float precision

7. **GTIN-13 Validation**:
   - Must be exactly 13 digits
   - Error if length is incorrect

8. **Brand Social Media (sameAs)**:
   - Must be an array
   - Should include Instagram, TikTok, or other platforms

9. **Description Length**:
   - Warn if less than 50 words
   - AI agents prefer fact-dense content

10. **Return Policy Links**:
    - `merchantReturnLink` must point to actual policy page
    - Should be accessible and match domain

11. **Shipping Details Completeness**:
    - Both `handlingTime` and `transitTime` required
    - Use quantitative values with unit code "d" (days)

12. **Date Formats**:
    - `priceValidUntil` must be YYYY-MM-DD
    - Should be future date (validation recommended)

### Legacy vs 2026 Schema

| Field | Legacy Support | 2026 UCP |
|-------|---------------|----------|
| `availability: "InStock"` | ⚠️ Warning | ❌ Error |
| `availability: "https://schema.org/InStock"` | ✅ Valid | ✅ Required |
| Missing `@id` | ⚠️ Warning | ❌ Error |
| Missing `gtin13` | - | ⚠️ UCP Missing |
| Missing return policy | - | ⚠️ UCP Missing |
| Missing shipping details | - | ⚠️ UCP Missing |
| Description < 50 words | - | ⚠️ Warning |

