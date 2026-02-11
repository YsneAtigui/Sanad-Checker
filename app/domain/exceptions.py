"""Domain-specific exceptions for the Sanad AEO Auditor.

These exceptions represent business logic errors and provide
structured error information with codes and context.
"""

from typing import Optional, Dict, Any


class AuditError(Exception):
    """Base exception for all audit-related errors.
    
    All custom domain exceptions inherit from this base class.
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize audit error.
        
        Args:
            message: Human-readable error message
            code: Error code for categorization (e.g., "AUDIT_001")
            context: Additional context data for debugging
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context
        }


class AuditNotFoundError(AuditError):
    """Raised when an audit job cannot be found."""
    
    def __init__(self, audit_id: str, **kwargs):
        message = f"Audit job not found: {audit_id}"
        super().__init__(
            message=message,
            code="AUDIT_NOT_FOUND",
            context={"audit_id": audit_id, **kwargs}
        )


class AuditValidationError(AuditError):
    """Raised when audit data fails validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="AUDIT_VALIDATION_ERROR",
            context={"field": field, **kwargs}
        )


class ExtractionError(AuditError):
    """Raised when content extraction fails."""
    
    def __init__(self, url: str, reason: str, **kwargs):
        message = f"Failed to extract content from {url}: {reason}"
        super().__init__(
            message=message,
            code="EXTRACTION_ERROR",
            context={"url": url, "reason": reason, **kwargs}
        )


class SchemaValidationError(AuditError):
    """Raised when JSON-LD schema validation fails."""
    
    def __init__(self, message: str, schema_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="SCHEMA_VALIDATION_ERROR",
            context={"schema_type": schema_type, **kwargs}
        )


class ProtocolCheckError(AuditError):
    """Raised when AEO protocol checks fail."""
    
    def __init__(self, protocol: str, reason: str, **kwargs):
        message = f"Protocol check failed for {protocol}: {reason}"
        super().__init__(
            message=message,
            code="PROTOCOL_CHECK_ERROR",
            context={"protocol": protocol, "reason": reason, **kwargs}
        )


class ServiceUnavailableError(AuditError):
    """Raised when an external service is unavailable."""
    
    def __init__(self, service: str, reason: str, **kwargs):
        message = f"Service unavailable: {service} - {reason}"
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            context={"service": service, "reason": reason, **kwargs}
        )


class RateLimitError(AuditError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, resource: str, retry_after: Optional[int] = None, **kwargs):
        message = f"Rate limit exceeded for {resource}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            context={"resource": resource, "retry_after": retry_after, **kwargs}
        )


class ContentAnalysisError(AuditError):
    """Raised when content analysis fails."""
    
    def __init__(self, message: str, analyzer: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="CONTENT_ANALYSIS_ERROR",
            context={"analyzer": analyzer, **kwargs}
        )


class ConfigurationError(AuditError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, setting: str, reason: str, **kwargs):
        message = f"Configuration error for '{setting}': {reason}"
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            context={"setting": setting, "reason": reason, **kwargs}
        )
