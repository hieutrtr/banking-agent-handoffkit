"""Validation utilities for HandoffKit."""

import re
from typing import Any, Optional

from handoffkit.core.exceptions import ConfigurationError


def validate_api_key(key: Optional[str], provider: str) -> bool:
    """Validate API key format for a provider.

    Args:
        key: API key to validate.
        provider: Provider name (zendesk, intercom, openai, etc.)

    Returns:
        True if key format is valid.

    Raises:
        ConfigurationError: If key is invalid.
    """
    if not key:
        raise ConfigurationError(f"API key required for {provider}")

    # Basic length validation
    if len(key) < 10:
        raise ConfigurationError(f"API key too short for {provider}")

    return True


def validate_url(url: Optional[str]) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate.

    Returns:
        True if URL is valid.
    """
    if not url:
        return False

    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def validate_email(email: Optional[str]) -> bool:
    """Validate email format.

    Args:
        email: Email to validate.

    Returns:
        True if email format is valid.
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input.

    Args:
        value: String to sanitize.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    # Remove control characters
    sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")
    # Truncate to max length
    return sanitized[:max_length]
