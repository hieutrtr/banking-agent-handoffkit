"""HandoffKit Core Module.

Contains the main orchestrator, configuration, types, and exceptions.
"""

from handoffkit.core.config import (
    HandoffConfig,
    IntegrationConfig,
    RoutingConfig,
    SentimentConfig,
    TriggerConfig,
)
from handoffkit.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ContextPackagingError,
    HandoffKitError,
    IntegrationError,
    RateLimitError,
    RoutingError,
    SentimentAnalysisError,
    TriggerError,
)
from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    SentimentResult,
    TriggerResult,
    TriggerType,
)

__all__ = [
    # Orchestrator
    "HandoffOrchestrator",
    # Configuration
    "HandoffConfig",
    "TriggerConfig",
    "SentimentConfig",
    "RoutingConfig",
    "IntegrationConfig",
    # Types
    "Message",
    "ConversationContext",
    "TriggerResult",
    "TriggerType",
    "SentimentResult",
    "HandoffDecision",
    "HandoffResult",
    "HandoffPriority",
    "HandoffStatus",
    # Exceptions
    "HandoffKitError",
    "ConfigurationError",
    "TriggerError",
    "SentimentAnalysisError",
    "ContextPackagingError",
    "RoutingError",
    "IntegrationError",
    "RateLimitError",
    "AuthenticationError",
]
