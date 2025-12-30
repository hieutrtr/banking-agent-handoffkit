"""HandoffKit Structured Logging Utilities.

This module provides structured JSON logging for HandoffKit with configurable
verbosity and machine-parseable output format.

Configuration via environment variables:
- LOG_LEVEL or HANDOFFKIT_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- LOG_FORMAT or HANDOFFKIT_LOG_FORMAT: "json" (default) or "text"

Example usage:
    >>> from handoffkit.utils.logging import setup_logging, get_logger
    >>> setup_logging()  # Configure with env vars
    >>> logger = get_logger("orchestrator")
    >>> logger.info("Handoff created", extra={"handoff_id": "abc123"})

JSON Output Format:
    {
        "timestamp": "2025-12-30T08:00:00.000000",
        "level": "INFO",
        "logger": "handoffkit.orchestrator",
        "message": "Handoff created",
        "module": "orchestrator",
        "function": "create_handoff",
        "handoff_id": "abc123"
    }
"""

import json
import logging
import os
import re
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional


# Custom fields that should be included in JSON output when present
CUSTOM_FIELDS = (
    "handoff_id",
    "user_id",
    "session_id",
    "trigger_type",
    "confidence",
    "duration_ms",
    "conversation_length",
    "helpdesk",
    "status_code",
    "error",
)

# Flag to track if logging has been set up
_logging_configured = False


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for machine parsing.

    This formatter outputs log records as JSON objects with a consistent
    structure including timestamp, level, logger name, message, and any
    custom fields provided via the `extra` parameter.

    Attributes:
        timestamp_format: The datetime format (always ISO 8601)

    Example:
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(JSONFormatter())
        >>> logger.addHandler(handler)
        >>> logger.info("Test message", extra={"user_id": "123"})
        {"timestamp": "2025-12-30T08:00:00.000000Z", "level": "INFO", ...}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON string representation of the log record.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else None
            )

        # Add custom fields from extra dict
        for field in CUSTOM_FIELDS:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Standard text formatter for human-readable logs.

    This is the default Python logging format, useful for development
    and debugging when JSON is not needed.
    """

    def __init__(self) -> None:
        """Initialize the text formatter with a standard format."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def _get_log_level() -> int:
    """Get the log level from environment variables.

    Checks HANDOFFKIT_LOG_LEVEL first, then LOG_LEVEL, defaults to INFO.

    Returns:
        The logging level as an integer.
    """
    level_str = os.environ.get(
        "HANDOFFKIT_LOG_LEVEL", os.environ.get("LOG_LEVEL", "INFO")
    ).upper()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_map.get(level_str, logging.INFO)


def _get_log_format() -> str:
    """Get the log format from environment variables.

    Checks HANDOFFKIT_LOG_FORMAT first, then LOG_FORMAT, defaults to "json".

    Returns:
        The format string ("json" or "text").
    """
    format_str = os.environ.get(
        "HANDOFFKIT_LOG_FORMAT", os.environ.get("LOG_FORMAT", "json")
    ).lower()

    if format_str not in ("json", "text"):
        return "json"

    return format_str


def setup_logging(
    level: Optional[int] = None,
    log_format: Optional[str] = None,
    force: bool = False,
) -> None:
    """Configure HandoffKit logging with structured output.

    Sets up the handoffkit logger with either JSON or text formatting
    based on environment variables or explicit parameters.

    Args:
        level: Logging level (overrides environment variable if provided).
        log_format: "json" or "text" (overrides environment variable if provided).
        force: Force reconfiguration even if already configured.

    Example:
        >>> setup_logging()  # Uses env vars
        >>> setup_logging(level=logging.DEBUG, log_format="text")
    """
    global _logging_configured

    if _logging_configured and not force:
        return

    # Get configuration from env vars or parameters
    log_level = level if level is not None else _get_log_level()
    fmt = log_format if log_format is not None else _get_log_format()

    # Get the handoffkit logger
    logger = logging.getLogger("handoffkit")
    logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create and configure handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    if fmt == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    _logging_configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for HandoffKit.

    Returns a child logger under the "handoffkit" namespace. If logging
    has not been configured, it will be auto-configured with defaults.

    Args:
        name: Logger name suffix (e.g., "orchestrator" -> "handoffkit.orchestrator").
              If None, returns the root "handoffkit" logger.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = get_logger("orchestrator")
        >>> logger.info("Starting orchestrator")
    """
    # Auto-initialize logging if not already done
    if not _logging_configured:
        setup_logging()

    logger_name = f"handoffkit.{name}" if name else "handoffkit"
    return logging.getLogger(logger_name)


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """Configure HandoffKit logging (legacy compatibility function).

    This function is maintained for backward compatibility with existing code.
    New code should use setup_logging() instead.

    Args:
        level: Logging level.
        format_string: Custom format string (ignored, uses JSON by default).
    """
    # Determine format - if format_string provided, use text
    log_format = "text" if format_string else "json"
    setup_logging(level=level, log_format=log_format, force=True)


class LogContext:
    """Context manager for adding contextual fields to log records.

    Provides a way to add consistent extra fields to all log records
    within a context block.

    Example:
        >>> with LogContext(handoff_id="abc123", user_id="user456"):
        ...     logger.info("Processing handoff")  # Includes handoff_id and user_id
    """

    _context: dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        """Initialize log context with extra fields.

        Args:
            **kwargs: Extra fields to add to log records.
        """
        self._fields = kwargs
        self._previous: dict[str, Any] = {}

    def __enter__(self) -> "LogContext":
        """Enter the context and store previous values."""
        self._previous = LogContext._context.copy()
        LogContext._context.update(self._fields)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context and restore previous values."""
        LogContext._context = self._previous

    @classmethod
    def get_context(cls) -> dict[str, Any]:
        """Get the current context fields.

        Returns:
            Dictionary of current context fields.
        """
        return cls._context.copy()


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any,
) -> None:
    """Log a message with extra context fields.

    Combines the current LogContext fields with any explicitly provided
    extra fields and logs the message.

    Args:
        logger: The logger to use.
        level: The logging level.
        message: The log message.
        **extra: Additional fields to include in the log record.

    Example:
        >>> log_with_context(logger, logging.INFO, "Handoff created",
        ...                  handoff_id="abc123", confidence=0.85)
    """
    combined_extra = {**LogContext.get_context(), **extra}
    logger.log(level, message, extra=combined_extra)


@contextmanager
def log_duration(
    logger: logging.Logger,
    operation: str,
    level: int = logging.DEBUG,
    **extra: Any,
) -> Generator[None, None, None]:
    """Context manager to log the duration of an operation.

    Logs the start and end of an operation, including the duration in
    milliseconds.

    Args:
        logger: The logger to use.
        operation: Name of the operation being timed.
        level: The logging level (default: DEBUG).
        **extra: Additional fields to include in the log records.

    Yields:
        None

    Example:
        >>> with log_duration(logger, "trigger_evaluation", trigger_type="sentiment"):
        ...     # Perform operation
        ...     pass
        # Logs: "trigger_evaluation completed" with duration_ms
    """
    start_time = time.perf_counter()
    log_with_context(logger, level, f"{operation} started", **extra)

    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        log_with_context(
            logger,
            level,
            f"{operation} completed",
            duration_ms=round(duration_ms, 2),
            **extra,
        )


# PII masking patterns
_ACCOUNT_PATTERN = re.compile(r"\b\d{8,16}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
_SSN_PATTERN = re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b")


def mask_pii(text: str) -> str:
    """Mask personally identifiable information in text.

    Masks account numbers, email addresses, phone numbers, and SSNs
    to prevent sensitive data from appearing in logs.

    Args:
        text: The text to mask.

    Returns:
        Text with PII replaced by masked versions.

    Example:
        >>> mask_pii("Account 12345678 for user@example.com")
        'Account ****5678 for u***@example.com'
    """
    result = text

    # Mask account numbers (show last 4 digits)
    def mask_account(match: re.Match[str]) -> str:
        num = match.group()
        if len(num) >= 4:
            return "****" + num[-4:]
        return "****"

    result = _ACCOUNT_PATTERN.sub(mask_account, result)

    # Mask email addresses (show first char and domain)
    def mask_email(match: re.Match[str]) -> str:
        email = match.group()
        at_index = email.index("@")
        if at_index > 0:
            return email[0] + "***" + email[at_index:]
        return "***" + email[at_index:]

    result = _EMAIL_PATTERN.sub(mask_email, result)

    # Mask phone numbers
    result = _PHONE_PATTERN.sub("***-***-****", result)

    # Mask SSNs
    result = _SSN_PATTERN.sub("***-**-****", result)

    return result


def is_logging_configured() -> bool:
    """Check if logging has been configured.

    Returns:
        True if setup_logging() has been called.
    """
    return _logging_configured


def reset_logging() -> None:
    """Reset logging configuration (mainly for testing).

    Removes all handlers from the handoffkit logger and resets
    the configured flag.
    """
    global _logging_configured

    logger = logging.getLogger("handoffkit")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    _logging_configured = False
    LogContext._context = {}
