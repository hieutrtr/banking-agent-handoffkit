"""HandoffKit Exception Definitions."""


class HandoffKitError(Exception):
    """Base exception for all HandoffKit errors."""

    pass


class ConfigurationError(HandoffKitError):
    """Raised when configuration is invalid."""

    pass


class TriggerError(HandoffKitError):
    """Raised when trigger evaluation fails."""

    pass


class SentimentAnalysisError(HandoffKitError):
    """Raised when sentiment analysis fails."""

    pass


class ContextPackagingError(HandoffKitError):
    """Raised when context packaging fails."""

    pass


class RoutingError(HandoffKitError):
    """Raised when agent routing fails."""

    pass


class IntegrationError(HandoffKitError):
    """Raised when helpdesk integration fails."""

    pass


class RateLimitError(HandoffKitError):
    """Raised when rate limits are exceeded."""

    pass


class AuthenticationError(HandoffKitError):
    """Raised when authentication fails."""

    pass
