"""
Structured logging configuration for the application.

Provides JSON-structured logging for production environments
and human-readable logs for development.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from functools import wraps


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack"] = self.formatException(record.stack_info)

        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


class StructuredLogger:
    """Structured logger for consistent logging across the application."""

    def __init__(
        self,
        name: str = "ai-underwriting",
        level: str = "INFO",
        json_format: bool = True,
    ):
        """Initialize structured logger."""
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.json_format = json_format
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logger with handlers and formatters."""
        self.logger.setLevel(self.level)
        self.logger.handlers = []

        handler = logging.StreamHandler(sys.stdout)

        if self.json_format:
            formatter = CustomJsonFormatter(
                "%(timestamp)s %(level)s %(message)s %(module)s %(function)s %(line)s"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """Log a message with optional extra fields."""
        self.logger.log(level, message, extra=extra, exc_info=exc_info)

    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a debug message."""
        self.log(logging.DEBUG, message, extra=extra)

    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an info message."""
        self.log(logging.INFO, message, extra=extra)

    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a warning message."""
        self.log(logging.WARNING, message, extra=extra)

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = True,
    ) -> None:
        """Log an error message."""
        self.log(logging.ERROR, message, extra=extra, exc_info=exc_info)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = True,
    ) -> None:
        """Log a critical message."""
        self.log(logging.CRITICAL, message, extra=extra, exc_info=exc_info)


def log_function_call(logger: Optional[StructuredLogger] = None):
    """Decorator to log function calls with arguments and return values."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or StructuredLogger(func.__module__)

            log.debug(
                f"Calling {func.__name__}",
                extra={"args": args, "kwargs": kwargs},
            )

            result = func(*args, **kwargs)

            log.debug(
                f"{func.__name__} returned",
                extra={"result": str(result)},
            )

            return result

        return wrapper

    return decorator


class RequestLogger:
    """Middleware for logging HTTP requests."""

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """Initialize request logger."""
        self.logger = logger or StructuredLogger("http")

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log an HTTP request."""
        level = logging.INFO if status_code < 400 else logging.WARNING

        self.logger.log(
            level,
            f"{method} {path} {status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "request_id": request_id,
                "type": "http_request",
            },
        )


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
) -> StructuredLogger:
    """
    Setup application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
        log_file: Optional file path to also log to file

    Returns:
        Configured StructuredLogger instance
    """
    logger = StructuredLogger(
        name="ai-underwriting",
        level=level,
        json_format=json_format,
    )

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))

        if json_format:
            file_formatter = CustomJsonFormatter(
                "%(timestamp)s %(level)s %(message)s"
            )
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(file_formatter)
        logger.logger.addHandler(file_handler)

    return logger
