"""HandoffKit - AI-to-human handoff orchestration SDK.

HandoffKit provides a framework-agnostic SDK for seamlessly transitioning
conversations from AI agents to human support representatives.

Quick Start:
    from handoffkit import HandoffOrchestrator, HandoffConfig

    orchestrator = HandoffOrchestrator(helpdesk="zendesk")
    should_handoff, trigger = orchestrator.should_handoff(messages, current_message)

    if should_handoff:
        result = orchestrator.create_handoff(messages, metadata={"user_id": "123"})

Configuration from Environment/File:
    # Load config from environment variables and config files
    from handoffkit import load_config, HandoffOrchestrator

    config = load_config()
    orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

    # Or use factory methods:
    orchestrator = HandoffOrchestrator.from_env()
    orchestrator = HandoffOrchestrator.from_file("config.yaml")

Logging Configuration:
    from handoffkit import setup_logging, get_logger

    # Configure logging (auto-configured on first orchestrator use)
    setup_logging()  # Uses LOG_LEVEL and LOG_FORMAT env vars

    # Get a logger for custom components
    logger = get_logger("my_component")
    logger.info("Custom message", extra={"user_id": "123"})
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
from handoffkit.core.config_loader import ConfigLoader, load_config
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
from handoffkit.utils.logging import get_logger, setup_logging

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
    # Configuration loading
    "ConfigLoader",
    "load_config",
    # Logging
    "setup_logging",
    "get_logger",
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
