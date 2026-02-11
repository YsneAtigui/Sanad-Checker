"""Unit tests for SchemaService.

Tests schema validation functionality with proper mocking.
"""

import pytest
import json

from app.services.schema_standardized import SchemaService
from app.application.dto import SchemaResponse, SchemaFieldResult
from app.domain.exceptions import SchemaValidationError
from app.domain.constants import STATUS_MATCH, STATUS_MISSING


@pytest.fixture
def schema_service():
    """Create SchemaService instance for testing."""
    return SchemaService()


@pytest.fixture
def valid_product_schema():
    """Mock valid Product schema."""
    return {
        "@type": "Product",
        "name": "Premium Widget",
        "brand": "WidgetCo",
        "description": "High quality widget for all your needs",
        "image": "https://example.com/widget.jpg",
        "offers": {
            "price": "99.99",
            "priceCurrency": "USD",
            "availability": "InStock"
        }
    }


@pytest.fixture
def incomplete_product_schema():
    """Mock incomplete Product schema."""
    return {
        "@type": "Product",
        "name": "Basic Widget",
        # Missing: brand, description, image, offers
    }


def test_validate_product_schema_success(schema_service, valid_product_schema):
    """Test successful schema validation with all required fields."""
    jsonld_data = [valid_product_schema]
    
    result = schema_service.validate_product_schema(jsonld_data, "")
    
    # Assert type
    assert isinstance(result, SchemaResponse)
    
    # Assert schema type
    assert result.schema_type == "Product"
    
    # Assert extracted JSON-LD
    assert json.loads(result.extracted_jsonld)["@type"] == "Product"
    
    # Assert score (all 7 required fields present)
    assert result.score == 100
    
    # Assert fields
    assert len(result.fields) == 7
    assert all(isinstance(field, SchemaFieldResult) for field in result.fields)
    
    # Check that all required fields are present
    field_statuses = {f.field: f.status for f in result.fields}
    assert field_statuses["Product name"] == STATUS_MATCH
    assert field_statuses["Price"] == STATUS_MATCH
    assert field_statuses["Currency"] == STATUS_MATCH


def test_validate_product_schema_incomplete(schema_service, incomplete_product_schema):
    """Test schema validation with missing fields."""
    jsonld_data = [incomplete_product_schema]
    
    result = schema_service.validate_product_schema(jsonld_data, "")
    
    # Assert type
    assert isinstance(result, SchemaResponse)
    
    # Assert low score (only name present out of 7)
    assert result.score < 50
    
    # Check that missing fields are marked as missing
    field_statuses = {f.field: f.status for f in result.fields}
    assert field_statuses["Product name"] == STATUS_MATCH
    assert field_statuses["Brand"] == STATUS_MISSING
    assert field_statuses["Description"] == STATUS_MISSING


def test_validate_product_schema_no_product(schema_service):
    """Test schema validation with no Product schema."""
    jsonld_data = [{"@type": "Organization", "name": "Company"}]
    
    result = schema_service.validate_product_schema(jsonld_data, "")
    
    # Assert empty result
    assert result.schema_type == "Product"
    assert result.score == 0
    assert result.extracted_jsonld == ""
    assert len(result.fields) == 0


def test_validate_product_schema_empty_list(schema_service):
    """Test schema validation with empty JSON-LD list."""
    result = schema_service.validate_product_schema([], "")
    
    # Assert empty result
    assert result.score == 0
    assert len(result.fields) == 0


def test_validate_product_schema_invalid_json(schema_service):
    """Test schema validation with invalid JSON structure."""
    # Create a schema that will cause JSON encoding issues
    invalid_schema = {
        "@type": "Product",
        "name": "Test",
        "circular": None
    }
    # Make it circular
    invalid_schema["circular"] = invalid_schema
    
    jsonld_data = [invalid_schema]
    
    with pytest.raises(SchemaValidationError):
        schema_service.validate_product_schema(jsonld_data, "")


def test_find_product_schema(schema_service, valid_product_schema):
    """Test finding Product schema in JSON-LD data."""
    jsonld_data = [
        {"@type": "Organization"},
        valid_product_schema,
        {"@type": "WebPage"}
    ]
    
    found = schema_service._find_product_schema(jsonld_data)
    
    assert found is not None
    assert found["@type"] == "Product"
    assert found["name"] == "Premium Widget"


def test_find_product_schema_not_found(schema_service):
    """Test finding Product schema when not present."""
    jsonld_data = [
        {"@type": "Organization"},
        {"@type": "WebPage"}
    ]
    
    found = schema_service._find_product_schema(jsonld_data)
    
    assert found is None


def test_validate_fields_with_offers_list(schema_service):
    """Test field validation with offers as list."""
    product_schema = {
        "@type": "Product",
        "name": "Widget",
        "offers": [
            {
                "price": "99.99",
                "priceCurrency": "USD",
                "availability": "InStock"
            }
        ]
    }
    
    fields = schema_service._validate_fields(product_schema, "")
    
    # Check price fields extracted from list
    price_field = next(f for f in fields if f.field == "Price")
    assert price_field.status == STATUS_MATCH
    assert price_field.structured_value == "99.99"
