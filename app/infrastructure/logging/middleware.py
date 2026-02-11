"""FastAPI middleware for request correlation IDs.

Adds unique correlation IDs to each request for tracking across services.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.logging.logger import set_correlation_id, get_logger

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to each request.
    
    Generates a unique ID for each request and adds it to:
    - Response headers (X-Correlation-ID)
    - Logging context
    - Request state
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
            
        Returns:
            Response with correlation ID header
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set in context for logging
        set_correlation_id(correlation_id)
        
        # Add to request state for access in handlers
        request.state.correlation_id = correlation_id
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "correlation_id": correlation_id,
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log response
        logger.info(
            f"Response {response.status_code}",
            extra={
                "status_code": response.status_code,
                "correlation_id": correlation_id,
            }
        )
        
        return response
