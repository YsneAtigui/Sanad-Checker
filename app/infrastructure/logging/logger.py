"""Structured logging utilities for the application.

Provides correlation IDs, contextual logging, and performance metrics.
"""

import logging
import time
import json
from functools import wraps
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar
import sys

from app.config import settings

# Context variable for correlation ID (request tracking)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for production logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add extra fields from record
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.msg = f"[{correlation_id[:8]}] {record.msg}"
        
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger
        
    Example:
        ```python
        from app.infrastructure.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Starting process", extra={"user_id": 123})
        ```
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        if settings.DEBUG:
            # Pretty console format for development
            formatter = ConsoleFormatter(
                '%(levelname)s: %(name)s - %(message)s'
            )
        else:
            # JSON format for production
            formatter = StructuredFormatter()
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context.
    
    Args:
        correlation_id: Unique ID for request tracking
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance.
    
    Logs execution time and any errors that occur.
    
    Example:
        ```python
        from app.infrastructure.logging import log_performance, get_logger
        
        logger = get_logger(__name__)
        
        @log_performance
        def slow_operation():
            time.sleep(2)
            return "done"
        ```
    """
    logger = get_logger(func.__module__)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug(
            f"Starting {func_name}",
            extra={"function": func_name, "event": "start"}
        )
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                f"Completed {func_name}",
                extra={
                    "function": func_name,
                    "duration_ms": round(duration * 1000, 2),
                    "event": "complete"
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Failed {func_name}: {str(e)}",
                extra={
                    "function": func_name,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "event": "error"
                },
                exc_info=True
            )
            raise
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug(
            f"Starting {func_name}",
            extra={"function": func_name, "event": "start"}
        )
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                f"Completed {func_name}",
                extra={
                    "function": func_name,
                    "duration_ms": round(duration * 1000, 2),
                    "event": "complete"
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Failed {func_name}: {str(e)}",
                extra={
                    "function": func_name,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "event": "error"
                },
                exc_info=True
            )
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper


class LoggerMixin:
    """Mixin to add logger to service classes.
    
    Example:
        ```python
        from app.infrastructure.logging import LoggerMixin
        
        class MyService(LoggerMixin):
            def process(self):
                self.logger.info("Processing...")
        ```
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger
