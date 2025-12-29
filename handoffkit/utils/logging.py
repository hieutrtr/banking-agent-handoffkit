"""Logging utilities for HandoffKit."""

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for HandoffKit.

    Args:
        name: Logger name (defaults to 'handoffkit').

    Returns:
        Configured logger instance.
    """
    logger_name = f"handoffkit.{name}" if name else "handoffkit"
    return logging.getLogger(logger_name)


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """Configure HandoffKit logging.

    Args:
        level: Logging level.
        format_string: Custom format string.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=format_string)
    logger = logging.getLogger("handoffkit")
    logger.setLevel(level)
