"""Domain-level constants for business logic.

These constants define thresholds, weights, and values used
throughout the application's business logic.
"""

from typing import Dict

# ============================================================================
# SCORING THRESHOLDS
# ============================================================================

SCORE_EXCELLENT = 90
"""Score threshold for excellent rating (90-100)"""

SCORE_GOOD = 70
"""Score threshold for good rating (70-89)"""

SCORE_NEEDS_IMPROVEMENT = 50
"""Score threshold for needs improvement (50-69)"""

SCORE_POOR = 0
"""Score threshold for poor rating (0-49)"""


# ============================================================================
# SEVERITY WEIGHTS
# ============================================================================

SEVERITY_WEIGHTS: Dict[str, int] = {
    "critical": 10,
    "high": 5,
    "medium": 3,
    "low": 1,
    "info": 0
}
"""Point deductions per severity level"""


# ============================================================================
# REQUIRED SCHEMA FIELDS
# ============================================================================

PRODUCT_REQUIRED_FIELDS = [
    "name",
    "price",
    "priceCurrency",
    "availability",
    "brand",
    "image",
    "description"
]
"""Required fields for Product schema validation"""

PRODUCT_RECOMMENDED_FIELDS = [
    "sku",
    "gtin13",
    "aggregateRating",
    "offers",
    "review"
]
"""Recommended fields for Product schema"""


# ============================================================================
# AEO PROTOCOL FILES
# ============================================================================

AEO_PROTOCOL_FILES = {
    "llms_txt": ".well-known/llms.txt",
    "agent_card": ".well-known/agent-card.json",
    "robots_txt": "robots.txt"
}
"""Standard AEO protocol file paths"""


# ============================================================================
# CONTENT QUALITY THRESHOLDS
# ============================================================================

MIN_DESCRIPTION_LENGTH = 50
"""Minimum characters for product description"""

MAX_KEYWORD_DENSITY = 0.03
"""Maximum keyword density (3%)"""

MIN_READABILITY_SCORE = 60
"""Minimum readability score for human-first content"""


# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    "INVALID_URL": "Invalid URL format. Please provide a valid HTTP/HTTPS URL.",
    "EXTRACTION_FAILED": "Failed to extract content from the provided URL.",
    "SCHEMA_NOT_FOUND": "No structured data found on the page.",
    "INVALID_SCHEMA": "Structured data is invalid or malformed.",
    "SERVICE_TIMEOUT": "Request timed out. Please try again later.",
    "RATE_LIMIT": "Rate limit exceeded. Please wait before retrying.",
}
"""Standard error messages for common scenarios"""


# ============================================================================
# STATUS VALUES
# ============================================================================

STATUS_FOUND = "found"
STATUS_NOT_FOUND = "not_found"
STATUS_INVALID = "invalid"
STATUS_VALID = "valid"
STATUS_MATCH = "match"
STATUS_MISMATCH = "mismatch"
STATUS_MISSING = "missing"

"""Standard status values for checks"""
