"""Global Exception Handlers for FastAPI Application"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.infrastructure.logging import get_logger
from app.domain.exceptions import (
    AuditError,
    AuditNotFoundError,
    ServiceUnavailableError,
)

logger = get_logger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors from Pydantic models
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database-related errors
    """
    logger.error(f"Database error on {request.url.path}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )


async def redis_exception_handler(request: Request, exc: RedisError):
    """
    Handle Redis cache errors (non-critical, degrade gracefully)
    """
    logger.warning(f"Redis error on {request.url.path}: {str(exc)}")
    
    # Don't fail the request, just log the cache failure
    # The application should continue without cache
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "warning": "Cache unavailable",
            "message": "Request processed successfully, but caching is temporarily unavailable"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions
    """
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please contact support if this persists.",
            "path": str(request.url.path)
        }
    )


async def domain_exception_handler(request: Request, exc: AuditError):
    """
    Handle custom domain exceptions
    """
    logger.warning(
        f"Domain error on {request.url.path}: {exc.message}",
        extra={"error_code": exc.code, "context": exc.context}
    )
    
    # Map to appropriate HTTP status
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, AuditNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ServiceUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


def register_exception_handlers(app):
    """
    Register all custom exception handlers with FastAPI app
    
    Usage:
        from app.exceptions import register_exception_handlers
        register_exception_handlers(app)
    """
    from fastapi.exceptions import RequestValidationError
    from sqlalchemy.exc import SQLAlchemyError
    from redis.exceptions import RedisError
    
    # Domain exceptions (check first, before generic)
    app.add_exception_handler(AuditError, domain_exception_handler)
    
    # Framework exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(RedisError, redis_exception_handler)
    
    # Catch-all (last)
    app.add_exception_handler(Exception, general_exception_handler)
