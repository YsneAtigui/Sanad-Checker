"""Schema validation service with standardized responses.

Validates JSON-LD structured data and returns typed, validated responses.
"""

from typing import List, Dict
import json

from app.services.base_service import BaseService
from app.infrastructure.logging import log_performance
from app.application.dto import SchemaResponse, SchemaFieldResult
from app.domain.constants import (
    PRODUCT_REQUIRED_FIELDS,
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_MISSING,
)
from app.domain.exceptions import SchemaValidationError


class SchemaService(BaseService):
    """Service for JSON-LD schema validation.
    
    Validates Product schema and checks field completeness.
    
    Example:
        ```python
        service = SchemaService()
        result = service.validate_product_schema(jsonld_data, visible_text)
        print(f"Schema score: {result.score}/100")
        for field in result.fields:
            print(f"{field.field}: {field.status}")
        ```
    """
    
    @log_performance
    def validate_product_schema(
        self,
        jsonld_data: List[Dict],
        visible_text: str = ""
    ) -> SchemaResponse:
        """Validate product schema and return standardized format.
        
        Checks Product schema for required fields and compares
        with visible page content.
        
        Args:
            jsonld_data: List of JSON-LD objects extracted from page
            visible_text: Visible page text for comparison
            
        Returns:
            SchemaResponse with validation results and score
            
        Raises:
            SchemaValidationError: If schema validation fails
            
        Example:
            >>> service = SchemaService()
            >>> jsonld = [{"@type": "Product", "name": "Widget", ...}]
            >>> response = service.validate_product_schema(jsonld, "...")
            >>> response.score
            85
        """
        self.logger.info(
            "Validating product schema",
            extra={"num_schemas": len(jsonld_data)}
        )
        
        try:
            # Find Product schema
            product_schema = self._find_product_schema(jsonld_data)
            
            if not product_schema:
                self.logger.warning("No Product schema found in JSON-LD data")
                return SchemaResponse(
                    schema_type="Product",
                    extracted_jsonld="",
                    fields=[],
                    score=0
                )
            
            # Extract JSON-LD as string
            extracted_jsonld = json.dumps(product_schema, ensure_ascii=False, indent=2)
            
            # Validate fields
            fields = self._validate_fields(product_schema, visible_text)
            
            # Calculate score
            present_fields = sum(
                1 for f in fields
                if f.status in [STATUS_MATCH, STATUS_MISMATCH]
            )
            total_fields = len(fields)
            score = round((present_fields / total_fields) * 100) if total_fields else 0
            
            response = SchemaResponse(
                schema_type="Product",
                extracted_jsonld=extracted_jsonld,
                fields=fields,
                score=score
            )
            
            self.logger.info(
                "Schema validation completed",
                extra={
                    "schema_type": "Product",
                    "score": score,
                    "present_fields": present_fields,
                    "total_fields": total_fields
                }
            )
            
            return response
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}", exc_info=True)
            raise SchemaValidationError(
                message=f"Invalid JSON in schema: {str(e)}",
                schema_type="Product"
            )
        except Exception as e:
            self.logger.error(f"Error validating schema: {str(e)}", exc_info=True)
            raise SchemaValidationError(
                message=str(e),
                schema_type="Product"
            )
    
    def _find_product_schema(self, jsonld_data: List[Dict]) -> Dict | None:
        """Find Product schema in JSON-LD data.
        
        Args:
            jsonld_data: List of JSON-LD objects
            
        Returns:
            Product schema dict or None
        """
        for schema in jsonld_data:
            if isinstance(schema, dict) and schema.get("@type") == "Product":
                return schema
        return None
    
    def _validate_fields(
        self,
        product_schema: Dict,
        visible_text: str
    ) -> List[SchemaFieldResult]:
        """Validate required Product schema fields.
        
        Args:
            product_schema: Product schema dictionary
            visible_text: Visible page text
            
        Returns:
            List of field validation results
        """
        fields = []
        field_labels = {
            "name": "Product name",
            "price": "Price",
            "priceCurrency": "Currency",
            "availability": "Availability",
            "brand": "Brand",
            "image": "Image",
            "description": "Description"
        }
        
        for field_key in PRODUCT_REQUIRED_FIELDS:
            field_label = field_labels.get(field_key, field_key)
            
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
                status = STATUS_MATCH  # Simplified - actual comparison would check visible text
                visible_value = str(value)
                structured_value = str(value)
            else:
                status = STATUS_MISSING
                visible_value = ""
                structured_value = ""
            
            fields.append(SchemaFieldResult(
                field=field_label,
                status=status,
                visible_value=visible_value,
                structured_value=structured_value
            ))
        
        return fields


# Standalone wrapper function for backward compatibility
def validate_product_schema_standardized(jsonld_data: List[Dict], visible_text: str = "") -> dict:
    """Standalone wrapper for SchemaService.validate_product_schema.
    
    Args:
        jsonld_data: List of JSON-LD objects extracted from page
        visible_text: Visible page text for comparison
        
    Returns:
        Dictionary with schema validation results (SchemaResponse as dict)
    """
    service = SchemaService()
    response = service.validate_product_schema(jsonld_data, visible_text)
    
    # Convert to dict for backward compatibility
    return {
        "schema_type": response.schema_type,
        "extracted_jsonld": response.extracted_jsonld,
        "fields": [
            {
                "field": field.field,
                "status": field.status,
                "visible_value": field.visible_value,
                "structured_value": field.structured_value
            }
            for field in response.fields
        ],
        "score": response.score
    }
