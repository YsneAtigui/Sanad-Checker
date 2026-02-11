"""Infrastructure-level constants for technical configuration.

These constants define timeouts, retry behavior, cache TTLs,
and other infrastructure-related values.
"""

# ============================================================================
# HTTP TIMEOUTS (seconds)
# ============================================================================

DEFAULT_HTTP_TIMEOUT = 30
"""Default timeout for HTTP requests"""

CRAWLER_TIMEOUT = 60
"""Timeout for web crawling operations"""

API_TIMEOUT = 10
"""Timeout for external API calls"""

OLLAMA_TIMEOUT = 120
"""Timeout for Ollama LLM requests"""


# ============================================================================
# RETRY CONFIGURATION
# ============================================================================

MAX_RETRIES = 3
"""Maximum number of retry attempts"""

RETRY_DELAY = 2
"""Base delay between retries (seconds)"""

RETRY_BACKOFF_MULTIPLIER = 2
"""Exponential backoff multiplier"""


# ============================================================================
# CACHE TTLs (seconds)
# ============================================================================

CACHE_TTL_SHORT = 300  # 5 minutes
"""Short-lived cache (frequently changing data)"""

CACHE_TTL_MEDIUM = 1800  # 30 minutes
"""Medium-lived cache (moderate update frequency)"""

CACHE_TTL_LONG = 3600  # 1 hour
"""Long-lived cache (rarely changing data)"""

CACHE_TTL_AUDIT = 3600  # 1 hour
"""Cache TTL for audit results"""

CACHE_TTL_ANALYTICS = 600  # 10 minutes
"""Cache TTL for analytics data"""


# ============================================================================
# RATE LIMITING
# ============================================================================

RATE_LIMIT_REQUESTS = 100
"""Maximum requests per window"""

RATE_LIMIT_WINDOW = 3600  # 1 hour
"""Rate limit time window (seconds)"""


# ============================================================================
# BATCH PROCESSING
# ============================================================================

BATCH_SIZE = 10
"""Default batch size for bulk operations"""

MAX_CONCURRENT_TASKS = 5
"""Maximum concurrent background tasks"""


# ============================================================================
# FILE SIZE LIMITS
# ============================================================================

MAX_HTML_SIZE = 10 * 1024 * 1024  # 10 MB
"""Maximum HTML file size to process"""

MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024  # 5 MB
"""Maximum screenshot size"""


# ============================================================================
# LOGGING
# ============================================================================

LOG_FORMAT_CONSOLE = "%(levelname)s: %(message)s"
"""Console log format (development)"""

LOG_FORMAT_JSON = "json"
"""JSON log format (production)"""

LOG_MAX_LENGTH = 10000
"""Maximum characters to log for large payloads"""
