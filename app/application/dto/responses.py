"""Response DTOs (Data Transfer Objects) for service layer.

These Pydantic models provide type-safe, validated response structures
for all service operations. They ensure consistent API responses and
enable automatic OpenAPI documentation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal


# ============================================================================
# PROTOCOL CHECK RESPONSES
# ============================================================================

class ProtocolCheckResult(BaseModel):
    """Individual protocol check result.
    
    Attributes:
        name: Protocol file name (e.g., "llms.txt")
        status: Check status (found, not_found, invalid, valid)
        detail: Human-readable detail message
        raw_content: Raw file content if found
    """
    name: str
    status: str
    detail: str
    raw_content: str = ""


class ProtocolResponse(BaseModel):
    """Standardized protocol check response.
    
    Attributes:
        checks: List of individual protocol check results
        score: Overall protocol compliance score (0-100)
    """
    checks: List[ProtocolCheckResult]
    score: int = Field(ge=0, le=100, description="Protocol compliance score")


# ============================================================================
# SCHEMA VALIDATION RESPONSES
# ============================================================================

class SchemaFieldResult(BaseModel):
    """Individual schema field validation result.
    
    Attributes:
        field: Field name (e.g., "Product name")
        status: Validation status (match, mismatch, missing)
        visible_value: Value visible on page
        structured_value: Value in structured data
    """
    field: str
    status: str
    visible_value: str
    structured_value: str


class SchemaResponse(BaseModel):
    """Standardized schema validation response.
    
    Attributes:
        schema_type: Schema type (e.g., "Product")
        extracted_jsonld: Raw JSON-LD as string
        fields: List of field validation results
        score: Schema completeness score (0-100)
    """
    schema_type: str
    extracted_jsonld: str
    fields: List[SchemaFieldResult]
    score: int = Field(ge=0, le=100, description="Schema completeness score")


# ============================================================================
# CONTENT QUALITY RESPONSES
# ============================================================================

class ContentIssue(BaseModel):
    """Content quality issue.
    
    Attributes:
        type: Issue type (e.g., "robotic_pattern", "keyword_stuffing")
        severity: Issue severity (critical, high, medium, low)
        description: Human-readable description
        location: Where the issue was found
    """
    type: str
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    location: str


class ContentResponse(BaseModel):
    """Standardized content quality response.
    
    Attributes:
        aeo_readiness_score: AEO readiness score (0-100)
        robotic_pattern_score: Robotic pattern level (Low, Medium, High)
        issues: List of content quality issues
        score: Overall content score (0-100)
    """
    aeo_readiness_score: int = Field(ge=0, le=100)
    robotic_pattern_score: Literal["Low", "Medium", "High"]
    issues: List[ContentIssue]
    score: int = Field(ge=0, le=100, description="Overall content quality score")


# ============================================================================
# EDGE VISIBILITY RESPONSES
# ============================================================================

class AgentAccessResult(BaseModel):
    """AI agent accessibility result.
    
    Attributes:
        name: Agent name (e.g., "ChatGPT")
        icon: Emoji icon for display
        status: Access status (accessible, blocked, degraded)
        response_time_ms: Response time in milliseconds
        data_completeness: Data completeness level (Full, Partial, None)
    """
    name: str
    icon: str
    status: Literal["accessible", "blocked", "degraded"]
    response_time_ms: int = Field(ge=0)
    data_completeness: Literal["Full", "Partial", "None"]


class EdgeResponse(BaseModel):
    """Standardized edge visibility response.
    
    Attributes:
        agents: List of agent accessibility results
        cloudflare_detected: Whether Cloudflare was detected
        bot_challenge_enabled: Whether bot challenges are enabled
        score: Accessibility score (0-100)
    """
    agents: List[AgentAccessResult]
    cloudflare_detected: bool
    bot_challenge_enabled: bool
    score: int = Field(ge=0, le=100, description="Accessibility score")


# ============================================================================
# ANALYTICS RESPONSES
# ============================================================================

class PlatformDistribution(BaseModel):
    """Platform distribution item.
    
    Attributes:
        platform: Platform name
        count: Number of audits
    """
    platform: str
    count: int


class StatusDistribution(BaseModel):
    """Status distribution item.
    
    Attributes:
        status: Audit status
        count: Number of audits
    """
    status: str
    count: int


class ScoreDistribution(BaseModel):
    """Score distribution item.
    
    Attributes:
        range: Score range (e.g., "0-20")
        count: Number of audits
    """
    range: str
    count: int


class AnalyticsResponse(BaseModel):
    """Standardized analytics response.
    
    Attributes:
        total_audits: Total number of audits
        completed_audits: Number of completed audits
        average_score: Average audit score
        platform_distribution: Distribution by platform
        status_distribution: Distribution by status
        score_distribution: Distribution by score range
    """
    total_audits: int = Field(ge=0)
    completed_audits: int = Field(ge=0)
    average_score: float = Field(ge=0, le=100)
    platform_distribution: List[PlatformDistribution]
    status_distribution: List[StatusDistribution]
    score_distribution: List[ScoreDistribution]


# ============================================================================
# EXTRACTION RESPONSES
# ============================================================================

class ExtractionResponse(BaseModel):
    """Content extraction response.
    
    Attributes:
        url: Extracted URL
        title: Page title
        markdown: Cleaned markdown content
        html_path: Path to saved HTML (optional)
        screenshot_path: Path to screenshot (optional)
    """
    url: str
    title: str
    markdown: str
    html_path: Optional[str] = None
    screenshot_path: Optional[str] = None


# ============================================================================
# REPORT RESPONSES
# ============================================================================

class ReportResponse(BaseModel):
    """Audit report response.
    
    Attributes:
        report_markdown: Full report in markdown
        summary: Executive summary
        overall_score: Overall audit score (0-100)
        recommendations_count: Number of recommendations
    """
    report_markdown: str
    summary: str
    overall_score: int = Field(ge=0, le=100)
    recommendations_count: int = Field(ge=0)
