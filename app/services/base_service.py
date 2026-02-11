"""Base service class for all services.

Provides common functionality including logging, dependency injection,
and utility methods.
"""

from abc import ABC
from typing import Optional

from app.infrastructure.logging import LoggerMixin
from app.infrastructure.constants import (
    DEFAULT_HTTP_TIMEOUT,
    CRAWLER_TIMEOUT,
    OLLAMA_TIMEOUT,
)
from app.config import settings


class BaseService(LoggerMixin, ABC):
    """Base class for all services.
    
    Provides:
    - Automatic logger injection via LoggerMixin
    - Common dependency management (Ollama, timeouts)
    - Shared utility methods
    
    Attributes:
        ollama_host: Ollama API endpoint URL
        ollama_model: Ollama model name
        http_timeout: Default HTTP request timeout (seconds)
        crawler_timeout: Web crawling timeout (seconds)
        
    Example:
        ```python
        class MyService(BaseService):
            async def process(self, data: str) -> Result:
                self.logger.info("Processing", extra={"data": data})
                # Use self.ollama_host, self.http_timeout, etc.
                return result
        ```
    """
    
    def __init__(
        self,
        ollama_host: Optional[str] = None,
        ollama_model: Optional[str] = None,
        http_timeout: Optional[int] = None,
        crawler_timeout: Optional[int] = None,
    ):
        """Initialize base service with common dependencies.
        
        Args:
            ollama_host: Ollama API endpoint (defaults to settings.OLLAMA_HOST)
            ollama_model: Ollama model name (defaults to settings.OLLAMA_MODEL)
            http_timeout: HTTP timeout in seconds (defaults to DEFAULT_HTTP_TIMEOUT)
            crawler_timeout: Crawler timeout in seconds (defaults to CRAWLER_TIMEOUT)
        """
        self.ollama_host = ollama_host or settings.OLLAMA_HOST
        self.ollama_model = ollama_model or settings.OLLAMA_MODEL
        self.http_timeout = http_timeout or DEFAULT_HTTP_TIMEOUT
        self.crawler_timeout = crawler_timeout or CRAWLER_TIMEOUT
    
    def _get_timeout_for(self, operation: str) -> int:
        """Get appropriate timeout for operation type.
        
        Args:
            operation: Operation type ("http", "crawler", "ollama")
            
        Returns:
            Timeout in seconds
        """
        timeouts = {
            "http": self.http_timeout,
            "crawler": self.crawler_timeout,
            "ollama": OLLAMA_TIMEOUT,
        }
        return timeouts.get(operation, self.http_timeout)
