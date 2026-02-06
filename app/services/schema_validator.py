"""JSON-LD Schema Validator Service

Validate e-commerce Product schema and ensure bilingual consistency.
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json
import re


# Middle East currencies
ME_CURRENCIES = ["SAR", "AED", "KWD", "BHD", "OMR", "QAR"]

# Valid schema.org availability values (2026 UCP: full URLs only)
VALID_AVAILABILITY = [
    "https://schema.org/InStock",
    "https://schema.org/OutOfStock",
    "https://schema.org/PreOrder",
    "https://schema.org/Discontinued",
    "https://schema.org/SoldOut",
    "https://schema.org/LimitedAvailability"
]

# Valid item conditions
VALID_ITEM_CONDITIONS = [
    "https://schema.org/NewCondition",
    "https://schema.org/UsedCondition",
    "https://schema.org/RefurbishedCondition",
    "https://schema.org/DamagedCondition"
]


def validate_product_schema(jsonld_data: List[Dict]) -> Dict:
    """
    Validate Product JSON-LD schema for 2026 UCP compliance
    
    Args:
        jsonld_data: List of JSON-LD blocks extracted from page
    
    Returns:
        Validation results with errors, warnings, UCP missing fields, and readiness score
    """
    
    # Find Product schema
    product_schema = find_product_schema(jsonld_data)
    
    if not product_schema:
        return {
            "valid": False,
            "found": False,
            "severity": "critical",
            "errors": ["No Product schema found on page"],
            "warnings": [],
            "ucp_missing": [],
            "ucp_readiness_score": 0.0,
            "ucp_compliant": False
        }
    
    errors = []
    warnings = []
    ucp_missing = []  # Highly recommended UCP fields
    
    # === CRITICAL REQUIRED FIELDS ===
    
    # Check @context
    if product_schema.get("@context") != "https://schema.org/":
        errors.append("Missing or incorrect '@context'. Must be 'https://schema.org/'")
    
    # Check @type
    schema_type = product_schema.get("@type")
    if schema_type != "Product":
        errors.append(f"Invalid @type: '{schema_type}' (expected 'Product')")
    
    # Check @id (unique canonical URL)
    if not product_schema.get("@id"):
        errors.append("Missing '@id' - unique canonical product URL required for UCP")
    elif "#product" not in product_schema["@id"]:
        warnings.append("@id should include fragment identifier (e.g., #product)")
    
    # Check name
    if not product_schema.get("name"):
        errors.append("Missing required field: 'name'")
    
    # Check description (50+ words recommended)
    description = product_schema.get("description", "")
    if not description:
        errors.append("Missing 'description' - required for AI citations")
    elif len(description.split()) < 50:
        warnings.append(f"Description too short ({len(description.split())} words). Aim for 50+ words for AI-friendly content")
    
    # Check SKU
    if not product_schema.get("sku"):
        errors.append("Missing required field: 'sku'")
    
    # Check image (array recommended)
    images = product_schema.get("image")
    if not images:
        errors.append("Missing required field: 'image'")
    elif isinstance(images, str):
        warnings.append("'image' should be an array of multiple product images")
    elif isinstance(images, list) and len(images) < 2:
        warnings.append("Only 1 image provided. Multiple images recommended for better visibility")
    
    # === VALIDATE OFFERS ===
    offers_validation = validate_offers(product_schema.get("offers"))
    errors.extend(offers_validation["errors"])
    warnings.extend(offers_validation["warnings"])
    ucp_missing.extend(offers_validation.get("ucp_missing", []))
    
    # === UCP HIGHLY RECOMMENDED FIELDS ===
    
    # Check GTIN-13
    if not product_schema.get("gtin13"):
        ucp_missing.append("gtin13 - GTIN-13 barcode increases product authority and trust")
    else:
        # Validate GTIN-13 length
        gtin = str(product_schema["gtin13"])
        if len(gtin) != 13:
            errors.append(f"Invalid gtin13 length: {len(gtin)}. Must be exactly 13 digits")
    
    # Check brand with social media
    brand = product_schema.get("brand", {})
    if not brand:
        ucp_missing.append("brand - Brand information increases authority")
    else:
        if isinstance(brand, dict):
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
    rating = product_schema.get("aggregateRating")
    if not rating:
        ucp_missing.append("aggregateRating - Reviews and ratings significantly improve AI visibility")
    else:
        if isinstance(rating, dict):
            if rating.get("@type") != "AggregateRating":
                warnings.append("aggregateRating.@type should be 'AggregateRating'")
            if not rating.get("ratingValue"):
                errors.append("Missing 'aggregateRating.ratingValue'")
            if not rating.get("reviewCount"):
                errors.append("Missing 'aggregateRating.reviewCount'")
    
    # === CALCULATE UCP READINESS SCORE ===
    # Based on 8 key UCP factors
    ucp_factors = {
        "gtin13": product_schema.get("gtin13"),
        "brand_with_social": brand.get("sameAs") if isinstance(brand, dict) else None,
        "aggregate_rating": rating,
        "return_policy": False,  # Will be set by offers validation
        "shipping_details": False,  # Will be set by offers validation
        "multiple_images": isinstance(images, list) and len(images) >= 2,
        "rich_description": len(description.split()) >= 50 if description else False,
        "item_condition": False  # Will be set by offers validation
    }
    
    # Check if offers has return policy and shipping (will be validated in validate_offers)
    offers = product_schema.get("offers")
    if offers:
        offer = offers[0] if isinstance(offers, list) else offers
        ucp_factors["return_policy"] = bool(offer.get("hasMerchantReturnPolicy"))
        ucp_factors["shipping_details"] = bool(offer.get("shippingDetails"))
        ucp_factors["item_condition"] = bool(offer.get("itemCondition"))
    
    total_checks = len(ucp_factors)
    present_checks = sum(1 for v in ucp_factors.values() if v)
    ucp_score = (present_checks / total_checks) * 100
    
    return {
        "valid": len(errors) == 0,
        "found": True,
        "severity": "critical" if errors else ("medium" if warnings else "none"),
        "errors": errors,
        "warnings": warnings,
        "ucp_missing": ucp_missing,
        "ucp_readiness_score": round(ucp_score, 1),
        "ucp_compliant": len(errors) == 0 and len(ucp_missing) == 0,
        "product_data": {
            "name": product_schema.get("name"),
            "price": get_price_from_offers(product_schema.get("offers")),
            "currency": get_currency_from_offers(product_schema.get("offers")),
            "availability": get_availability_from_offers(product_schema.get("offers"))
        }
    }


def find_product_schema(jsonld_data: List[Dict]) -> Optional[Dict]:
    """Find Product schema in JSON-LD data"""
    
    for block in jsonld_data:
        # Skip if block is not a dict
        if not isinstance(block, dict):
            # If it's a list, iterate through items
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
            continue
        
        # Direct Product type
        if block.get("@type") == "Product":
            return block
        
        # Handle @graph arrays
        if "@graph" in block:
            for item in block["@graph"]:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    return item
    
    return None


def validate_offers(offers) -> Dict:
    """Validate offers object/array with 2026 UCP requirements"""
    
    errors = []
    warnings = []
    ucp_missing = []
    
    if not offers:
        errors.append("Missing required field: 'offers'")
        return {"errors": errors, "warnings": warnings, "ucp_missing": ucp_missing}
    
    # Handle single offer or array of offers
    offer = offers
    if isinstance(offers, list):
        if len(offers) == 0:
            errors.append("Empty offers array")
            return {"errors": errors, "warnings": warnings, "ucp_missing": ucp_missing}
        offer = offers[0]
    
    # Check offer @type
    offer_type = offer.get("@type")
    if offer_type not in ["Offer", "AggregateOffer"]:
        warnings.append(f"offers.@type should be 'Offer' or 'AggregateOffer', got '{offer_type}'")
    
    # Check offer URL
    if not offer.get("url"):
        errors.append("Missing 'offers.url'")
    
    # Validate price based on offer type
    if offer_type == "AggregateOffer":
        # AggregateOffer uses lowPrice/highPrice instead of price
        low_price = offer.get("lowPrice")
        high_price = offer.get("highPrice")
        
        if not low_price and not high_price:
            errors.append("Missing 'offers.lowPrice' and 'offers.highPrice' for AggregateOffer")
        else:
            # Validate prices are numeric
            try:
                if low_price:
                    float(low_price)
                if high_price:
                    float(high_price)
            except (ValueError, TypeError):
                errors.append(f"Invalid price format in AggregateOffer")
    else:
        # Regular Offer uses price
        price = offer.get("price")
        if not price:
            errors.append("Missing 'offers.price'")
        else:
            # Validate price is numeric
            try:
                float(price)
            except (ValueError, TypeError):
                errors.append(f"Invalid price format: '{price}'")
    
    # Validate currency
    currency = offer.get("priceCurrency")
    if not currency:
        errors.append("Missing 'offers.priceCurrency'")
    elif currency not in ME_CURRENCIES:
        warnings.append(f"Non-Middle East currency: '{currency}' (expected: {', '.join(ME_CURRENCIES)})")
    
    # Check priceValidUntil (required for UCP)
    if not offer.get("priceValidUntil"):
        errors.append("Missing 'offers.priceValidUntil' (YYYY-MM-DD format)")
    else:
        # Validate date format
        price_valid = offer["priceValidUntil"]
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(price_valid)):
            errors.append(f"'priceValidUntil' must be in YYYY-MM-DD format, got '{price_valid}'")
    
    # Validate availability (must use full schema.org URL)
    availability = offer.get("availability")
    if not availability:
        errors.append("Missing 'offers.availability'")
    elif availability not in VALID_AVAILABILITY:
        # Check if it's shorthand (InStock instead of https://schema.org/InStock)
        if availability in ["InStock", "OutOfStock", "PreOrder", "SoldOut", "Discontinued"]:
            errors.append(f"Use full schema.org URL for availability: 'https://schema.org/{availability}' instead of '{availability}'")
        else:
            errors.append(f"Invalid availability: '{availability}'. Must use full schema.org URL")
    
    # Check itemCondition (recommended)
    if not offer.get("itemCondition"):
        warnings.append("Missing 'offers.itemCondition' - specify NewCondition, UsedCondition, etc.")
    elif offer["itemCondition"] not in VALID_ITEM_CONDITIONS:
        # Check if shorthand is used
        condition = offer["itemCondition"]
        if "NewCondition" in condition or "UsedCondition" in condition:
            warnings.append(f"Use full schema.org URL for itemCondition (e.g., 'https://schema.org/NewCondition')")
        else:
            warnings.append(f"Invalid itemCondition: '{condition}'")
    
    # === CHECK MERCHANT RETURN POLICY ===
    return_policy = offer.get("hasMerchantReturnPolicy", {})
    if not return_policy:
        ucp_missing.append("hasMerchantReturnPolicy - Return policy is critical for e-commerce trust signals")
    else:
        if isinstance(return_policy, dict):
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
                warnings.append("Missing 'returnMethod' (e.g., https://schema.org/ReturnByMail)")
            
            if not return_policy.get("returnFees"):
                warnings.append("Missing 'returnFees' (e.g., https://schema.org/FreeReturn)")
            
            if not return_policy.get("merchantReturnLink"):
                warnings.append("Missing 'merchantReturnLink' - link to full return policy page")
    
    # === CHECK SHIPPING DETAILS ===
    shipping = offer.get("shippingDetails", {})
    if not shipping:
        ucp_missing.append("shippingDetails - Shipping information is essential for e-commerce AI agents")
    else:
        if isinstance(shipping, dict):
            if shipping.get("@type") != "OfferShippingDetails":
                warnings.append("shippingDetails.@type should be 'OfferShippingDetails'")
            
            # Check shipping rate
            shipping_rate = shipping.get("shippingRate", {})
            if not shipping_rate:
                warnings.append("Missing 'shippingDetails.shippingRate'")
            else:
                if isinstance(shipping_rate, dict):
                    if not shipping_rate.get("value"):
                        warnings.append("Missing 'shippingRate.value'")
                    if not shipping_rate.get("currency"):
                        warnings.append("Missing 'shippingRate.currency'")
            
            # Check delivery time
            delivery_time = shipping.get("deliveryTime", {})
            if not delivery_time:
                warnings.append("Missing 'shippingDetails.deliveryTime'")
            else:
                if isinstance(delivery_time, dict):
                    # Check handling time
                    handling = delivery_time.get("handlingTime", {})
                    if not handling:
                        warnings.append("Missing 'deliveryTime.handlingTime'")
                    
                    # Check transit time
                    transit = delivery_time.get("transitTime", {})
                    if not transit:
                        warnings.append("Missing 'deliveryTime.transitTime'")
    
    return {"errors": errors, "warnings": warnings, "ucp_missing": ucp_missing}


def get_price_from_offers(offers) -> Optional[float]:
    """Extract price from offers (handles both Offer and AggregateOffer)"""
    if not offers:
        return None
    
    offer = offers[0] if isinstance(offers, list) else offers
    
    # Check if it's an AggregateOffer
    if offer.get("@type") == "AggregateOffer":
        # Use lowPrice, or highPrice if lowPrice not available
        price = offer.get("lowPrice") or offer.get("highPrice")
    else:
        # Regular Offer
        price = offer.get("price")
    
    try:
        return float(price)
    except (ValueError, TypeError):
        return None


def get_currency_from_offers(offers) -> Optional[str]:
    """Extract currency from offers"""
    if not offers:
        return None
    
    offer = offers[0] if isinstance(offers, list) else offers
    return offer.get("priceCurrency")


def get_availability_from_offers(offers) -> Optional[str]:
    """Extract availability from offers"""
    if not offers:
        return None
    
    offer = offers[0] if isinstance(offers, list) else offers
    return offer.get("availability")


def verify_metadata_language(page_lang: str, jsonld: Dict) -> Dict:
    """
    Check if metadata language matches page language
    
    Args:
        page_lang: 'ar' or 'en'
        jsonld: Product schema
    
    Returns:
        Validation result
    """
    
    name = jsonld.get("name", "")
    description = jsonld.get("description", "")
    
    # Arabic character detection (U+0600 to U+06FF)
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    has_arabic = bool(arabic_pattern.search(name + description))
    
    if page_lang == "ar" and not has_arabic:
        return {
            "valid": False,
            "severity": "high",
            "issue": "Arabic page (/ar) has non-Arabic metadata",
            "recommendation": "Use Arabic characters in name and description for Arabic pages"
        }
    
    if page_lang == "en" and has_arabic:
        return {
            "valid": False,
            "severity": "medium",
            "issue": "English page (/en) has Arabic metadata",
            "recommendation": "Use English characters in name and description for English pages"
        }
    
    return {"valid": True, "severity": "none"}


def compare_visible_vs_structured(visible_markdown: str, jsonld: Dict) -> Dict:
    """
    Compare visible page content with JSON-LD data to prevent hallucination
    
    Args:
        visible_markdown: Extracted Markdown content
        jsonld: Product schema
    
    Returns:
        Comparison results
    """
    
    mismatches = []
    
    # Extract price from visible content (simple regex)
    # Look for patterns like "32.99", "AED 32.99", "SAR 150"
    price_pattern = re.compile(r'(\d+[\.,]\d{2})')
    visible_prices = [float(p.replace(',', '.')) for p in price_pattern.findall(visible_markdown)]
    
    jsonld_price = get_price_from_offers(jsonld.get("offers"))
    
    if jsonld_price and visible_prices:
        # Check if JSON-LD price is in visible prices
        if not any(abs(vp - jsonld_price) < 0.01 for vp in visible_prices):
            mismatches.append({
                "field": "price",
                "severity": "critical",
                "visible_values": visible_prices,
                "structured_value": jsonld_price,
                "issue": "Price in JSON-LD does not match any visible price on page"
            })
    
    # Product name comparison (case-insensitive, normalized)
    product_name = jsonld.get("name", "")
    if product_name:
        # Normalize: lowercase, remove extra spaces
        normalized_name = " ".join(product_name.lower().split())
        normalized_visible = " ".join(visible_markdown.lower().split())
        
        if normalized_name not in normalized_visible:
            mismatches.append({
                "field": "name",
                "severity": "medium",
                "structured_value": product_name,
                "issue": "Product name from JSON-LD not found in visible content"
            })
    
    return {
        "matches": len(mismatches) == 0,
        "mismatches": mismatches,
        "severity": "critical" if any(m["severity"] == "critical" for m in mismatches) else ("medium" if mismatches else "none")
    }


def validate_bilingual_schemas(ar_jsonld: List[Dict], en_jsonld: List[Dict]) -> Dict:
    """
    Validate that both language versions have consistent Product schemas
    
    Args:
        ar_jsonld: Arabic page JSON-LD
        en_jsonld: English page JSON-LD
    
    Returns:
        Bilingual validation results
    """
    
    ar_product = find_product_schema(ar_jsonld)
    en_product = find_product_schema(en_jsonld)
    
    issues = []
    
    if not ar_product:
        issues.append({
            "severity": "critical",
            "issue": "Arabic page missing Product schema"
        })
    
    if not en_product:
        issues.append({
            "severity": "critical",
            "issue": "English page missing Product schema"
        })
    
    if ar_product and en_product:
        # Compare prices
        ar_price = get_price_from_offers(ar_product.get("offers"))
        en_price = get_price_from_offers(en_product.get("offers"))
        
        if ar_price and en_price and abs(ar_price - en_price) > 0.01:
            issues.append({
                "severity": "critical",
                "field": "price",
                "issue": f"Price mismatch between languages: AR={ar_price}, EN={en_price}"
            })
        
        # Compare currency
        ar_currency = get_currency_from_offers(ar_product.get("offers"))
        en_currency = get_currency_from_offers(en_product.get("offers"))
        
        if ar_currency != en_currency:
            issues.append({
                "severity": "high",
                "field": "currency",
                "issue": f"Currency mismatch: AR={ar_currency}, EN={en_currency}"
            })
        
        # Verify language-specific metadata
        ar_lang_check = verify_metadata_language("ar", ar_product)
        if not ar_lang_check["valid"]:
            issues.append({
                "severity": ar_lang_check["severity"],
                "field": "metadata_language",
                "issue": ar_lang_check["issue"]
            })
        
        en_lang_check = verify_metadata_language("en", en_product)
        if not en_lang_check["valid"]:
            issues.append({
                "severity": en_lang_check["severity"],
                "field": "metadata_language",
                "issue": en_lang_check["issue"]
            })
    
    return {
        "consistent": len(issues) == 0,
        "issues": issues,
        "severity": "critical" if any(i.get("severity") == "critical" for i in issues) else ("high" if issues else "none")
    }
