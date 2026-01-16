"""
Structured logging configuration for PathPilot.

Constitution Compliance:
- Principle V: Code Quality - Structured logging with request_id, user_id, operation, duration_ms
- Principle III: User Data Privacy - PII scrubbing (see privacy.py for scrubbing utilities)
"""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "pathpilot"
    event_dict["env"] = "development"  # Will be overridden by config
    return event_dict


def censor_sensitive_keys(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Censor sensitive data in logs.

    Constitution III: User Data Privacy - Never log API keys, passwords, or tokens.
    """
    sensitive_keys = {
        "password",
        "api_key",
        "token",
        "secret",
        "authorization",
        "google_api_key",
        "elevenlabs_api_key",
    }

    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***REDACTED***"

    return event_dict


def configure_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON format; otherwise, human-readable console format

    Constitution V: Structured logging with consistent fields:
    - request_id: UUID for request tracing
    - user_id: Anonymized user identifier
    - operation: Name of the operation being performed
    - duration_ms: Operation duration in milliseconds
    - level: Log level (DEBUG, INFO, WARNING, ERROR)
    - timestamp: ISO 8601 timestamp
    """

    # Shared processors for all configurations
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_app_context,
        censor_sensitive_keys,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console output for development
        processors = shared_processors + [
            structlog.processors.ExceptionRenderer(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str = "pathpilot") -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("resume_analysis_started", request_id="abc-123", user_id="user-456")
    """
    return structlog.get_logger(name)


# Example usage and patterns
if __name__ == "__main__":
    # Configure logging for development
    configure_logging(log_level="DEBUG", json_output=False)

    logger = get_logger(__name__)

    # Example: Resume upload
    logger.info(
        "resume_upload_started",
        request_id="req-123",
        user_id="user-456",
        operation="resume_upload",
        filename="john_doe_resume.pdf",
    )

    # Example: AI API call
    logger.info(
        "gemini_api_called",
        request_id="req-123",
        operation="resume_analysis",
        model="gemini-1.5-pro",
        tokens_requested=1000,
    )

    # Example: Operation complete with duration
    logger.info(
        "resume_analysis_completed",
        request_id="req-123",
        user_id="user-456",
        operation="resume_analysis",
        duration_ms=2345,
        success=True,
    )

    # Example: Error logging
    try:
        raise ValueError("Example error")
    except Exception:
        logger.error(
            "resume_parsing_failed",
            request_id="req-123",
            operation="resume_text_extraction",
            exc_info=True,
        )
