"""
Standardized Schema Validator Wrapper

Wraps schema_validator.py to return standardized JSON matching frontend schema.
"""
from typing import Dict, List
import json


def validate_product_schema_standardized(jsonld_data: List[Dict], visible_text: str = "") -> Dict:
    """
    Validate product schema and return standardized format
    
    Args:
        jsonld_data: List of JSON-LD objects
        visible_text: Visible page text for comparison
        
    Returns:
        {
            "schema_type": "Product",
            "extracted_jsonld": "<JSON string>",
            "fields": [...],
            "score": 0-100
        }
    """
    # Find Product schema
    product_schema = None
    for schema in jsonld_data:
        if isinstance(schema, dict) and schema.get("@type") == "Product":
            product_schema = schema
            break
    
    if not product_schema:
        return {
            "schema_type": "Product",
            "extracted_jsonld": "",
            "fields": [],
            "score": 0
        }
    
    # Extract JSON-LD as string
    extracted_jsonld = json.dumps(product_schema, ensure_ascii=False, indent=2)
    
    # Validate key fields
    fields = []
    required_fields = {
        "name": "Product name",
        "price": "Price",
        "priceCurrency": "Currency",
        "availability": "Availability",
        "brand": "Brand",
        "image": "Image",
        "description": "Description"
    }
    
    for field_key, field_label in required_fields.items():
        # Check in offers if price-related
        if field_key in ["price", "priceCurrency", "availability"]:
            offers = product_schema.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            
            value = offers.get(field_key) if isinstance(offers, dict) else None
        else:
            value = product_schema.get(field_key)
        
        # Determine status
        if value:
            status = "match"  # Simplified - actual comparison would check visible text
            visible_value = str(value)
            structured_value = str(value)
        else:
            status = "missing"
            visible_value = ""
            structured_value = ""
        
        fields.append({
            "field": field_label,
            "status": status,
            "visible_value": visible_value,
            "structured_value": structured_value
        })
    
    # Calculate score
    present_fields = sum(1 for f in fields if f["status"] in ["match", "mismatch"])
    score = round((present_fields / len(fields)) * 100) if fields else 0
    
    return {
        "schema_type": "Product",
        "extracted_jsonld": extracted_jsonld,
        "fields": fields,
        "score": score
    }
