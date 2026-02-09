"""Value objects for domain logic."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
import re


@dataclass(frozen=True)
class AuditURL:
    """Value object for validated URLs."""
    
    value: str
    
    def __post_init__(self):
        """Validate URL on creation."""
        if not self.value:
            raise ValueError("URL cannot be empty")
        
        # Basic URL validation
        parsed = urlparse(self.value)
        if not parsed.scheme in ("http", "https"):
            raise ValueError(f"URL must use http or https scheme, got: {parsed.scheme}")
        
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain")
    
    def get_domain(self) -> str:
        """Extract domain from URL."""
        parsed = urlparse(self.value)
        return parsed.netloc
    
    def is_https(self) -> bool:
        """Check if URL uses HTTPS."""
        return urlparse(self.value).scheme == "https"
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Platform:
    """Value object for e-commerce platform detection."""
    
    name: str
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate platform data."""
        known_platforms = ("salla", "zid", "shopify", "woocommerce", "magento", "unknown")
        if self.name.lower() not in known_platforms:
            object.__setattr__(self, "name", "unknown")
            object.__setattr__(self, "confidence", 0.0)
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    def is_known(self) -> bool:
        """Check if platform is known (not unknown)."""
        return self.name.lower() != "unknown"
    
    def __str__(self) -> str:
        if self.confidence < 1.0:
            return f"{self.name} ({self.confidence:.0%} confidence)"
        return self.name


@dataclass(frozen=True)
class SeverityLevel:
    """Unified severity value object."""
    
    level: str
    score_impact: int  # How much this severity impacts overall score
    
    def __post_init__(self):
        """Validate severity level."""
        valid_levels = {
            "critical": 25,
            "high": 15,
            "medium": 10,
            "low": 5
        }
        
        if self.level.lower() not in valid_levels:
            raise ValueError(f"Invalid severity level: {self.level}")
        
        # Set score impact based on level
        expected_impact = valid_levels[self.level.lower()]
        if self.score_impact != expected_impact:
            object.__setattr__(self, "score_impact", expected_impact)
    
    def is_critical(self) -> bool:
        """Check if severity is critical."""
        return self.level.lower() == "critical"
    
    def is_high_or_critical(self) -> bool:
        """Check if severity is high or critical."""
        return self.level.lower() in ("critical", "high")
    
    @classmethod
    def critical(cls) -> "SeverityLevel":
        """Create critical severity."""
        return cls(level="critical", score_impact=25)
    
    @classmethod
    def high(cls) -> "SeverityLevel":
        """Create high severity."""
        return cls(level="high", score_impact=15)
    
    @classmethod
    def medium(cls) -> "SeverityLevel":
        """Create medium severity."""
        return cls(level="medium", score_impact=10)
    
    @classmethod
    def low(cls) -> "SeverityLevel":
        """Create low severity."""
        return cls(level="low", score_impact=5)
    
    def __str__(self) -> str:
        return self.level.upper()
