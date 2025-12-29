"""HandoffKit - AI-to-human handoff orchestration SDK.

HandoffKit provides a framework-agnostic SDK for seamlessly transitioning
conversations from AI agents to human support representatives.

Quick Start:
    from handoffkit import HandoffOrchestrator, HandoffConfig

    orchestrator = HandoffOrchestrator(HandoffConfig())
    decision = await orchestrator.check_handoff_needed(message, context)

    if decision.should_handoff:
        result = await orchestrator.execute_handoff(conversation_context)
"""

__version__ = "0.1.0"

# Core exports
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
    MessageSpeaker,
    SentimentResult,
    TriggerResult,
    TriggerType,
)

__all__ = [
    # Version
    "__version__",
    # Main orchestrator
    "HandoffOrchestrator",
    # Configuration
    "HandoffConfig",
    "TriggerConfig",
    "SentimentConfig",
    "RoutingConfig",
    "IntegrationConfig",
    # Types
    "Message",
    "MessageSpeaker",
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
