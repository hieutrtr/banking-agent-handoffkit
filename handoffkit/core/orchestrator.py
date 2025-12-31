"""HandoffKit Core Orchestrator - Main entry point for handoff operations.

This module provides the HandoffOrchestrator class which is the primary interface
for AI-to-human handoff operations.

Example usage:
    >>> from handoffkit import HandoffOrchestrator, Message
    >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
    >>> messages = [Message(speaker="user", content="I need help")]
    >>> should_handoff, trigger = orchestrator.should_handoff(messages, "I need help")

    # Create from environment variables and config files
    >>> orchestrator = HandoffOrchestrator.from_env()
"""

import logging
from typing import Any, Optional

from handoffkit.core.config import HandoffConfig, TriggerConfig
from handoffkit.core.config_loader import ConfigLoader, load_config
from handoffkit.core.types import (
    HandoffResult,
    HandoffStatus,
    Message,
    TriggerResult,
)
from handoffkit.utils.logging import get_logger, log_with_context

# Valid helpdesk provider values
_VALID_HELPDESKS = {"zendesk", "intercom", "custom"}


class HandoffOrchestrator:
    """Main orchestrator for AI-to-human handoff operations.

    This is the primary entry point for HandoffKit functionality. It provides
    methods to detect when a conversation should be handed off to a human agent
    and to execute the handoff process.

    Attributes:
        helpdesk: The helpdesk provider to use (zendesk, intercom, custom)
        config: The configuration for this orchestrator
        triggers: Shortcut to config.triggers for trigger settings

    Example:
        >>> from handoffkit import HandoffOrchestrator, HandoffConfig, Message
        >>>
        >>> # Create with default settings
        >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        >>>
        >>> # Create with custom config
        >>> config = HandoffConfig(max_context_messages=50)
        >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)
        >>>
        >>> # Check if handoff is needed
        >>> messages = [Message(speaker="user", content="I need help")]
        >>> should_handoff, trigger = orchestrator.should_handoff(messages, "I need help")
        >>>
        >>> if should_handoff:
        ...     result = orchestrator.create_handoff(messages, metadata={"user_id": "123"})
    """

    def __init__(
        self,
        helpdesk: str = "zendesk",
        *,
        config: Optional[HandoffConfig] = None,
    ) -> None:
        """Initialize the orchestrator with helpdesk provider and optional configuration.

        Args:
            helpdesk: The helpdesk provider to use. Valid values are:
                      'zendesk', 'intercom', or 'custom'. Defaults to 'zendesk'.
            config: Optional HandoffConfig for customizing behavior.
                   If not provided, uses default configuration.

        Raises:
            ValueError: If helpdesk is not a valid provider value.

        Example:
            >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
            >>> orchestrator = HandoffOrchestrator(helpdesk="intercom", config=HandoffConfig())
        """
        # Validate helpdesk parameter
        if helpdesk not in _VALID_HELPDESKS:
            raise ValueError(
                f"Invalid helpdesk value '{helpdesk}'. "
                f"Valid options are: {', '.join(sorted(_VALID_HELPDESKS))}."
            )

        self._helpdesk = helpdesk
        self._config = config if config is not None else HandoffConfig()
        self._logger = get_logger("orchestrator")

        # Initialize ConversationPackager for context preservation
        # Late import to avoid circular dependency
        from handoffkit.context.packager import ConversationPackager

        self._context_packager = ConversationPackager(
            max_messages=self._config.max_context_messages,
            max_size_kb=self._config.max_context_size_kb,
        )

        # Log initialization at DEBUG level
        self._logger.debug(
            "Orchestrator initialized",
            extra={
                "helpdesk": self._helpdesk,
                "trigger_type": "initialization",
            },
        )

    @classmethod
    def from_env(
        cls,
        helpdesk: str = "zendesk",
    ) -> "HandoffOrchestrator":
        """Create an orchestrator with configuration from environment variables and config files.

        This factory method loads configuration from environment variables (HANDOFFKIT_*)
        and config files (handoffkit.yaml) with environment variables taking precedence.

        Args:
            helpdesk: The helpdesk provider to use. Defaults to 'zendesk'.

        Returns:
            A new HandoffOrchestrator with configuration loaded from external sources.

        Raises:
            ValueError: If helpdesk is not a valid provider value.
            ConfigurationError: If configuration values are invalid.

        Example:
            >>> import os
            >>> os.environ["HANDOFFKIT_FAILURE_THRESHOLD"] = "5"
            >>> orchestrator = HandoffOrchestrator.from_env()
            >>> orchestrator.triggers.failure_threshold
            5
        """
        config = load_config()
        return cls(helpdesk=helpdesk, config=config)

    @classmethod
    def from_file(
        cls,
        config_file: str,
        helpdesk: str = "zendesk",
    ) -> "HandoffOrchestrator":
        """Create an orchestrator with configuration from a specific file.

        This factory method loads configuration from the specified YAML config file.
        Environment variables are NOT loaded when using this method.

        Args:
            config_file: Path to the YAML configuration file.
            helpdesk: The helpdesk provider to use. Defaults to 'zendesk'.

        Returns:
            A new HandoffOrchestrator with configuration loaded from the file.

        Raises:
            ValueError: If helpdesk is not a valid provider value.
            ConfigurationError: If the file cannot be read or parsed.

        Example:
            >>> orchestrator = HandoffOrchestrator.from_file("config/production.yaml")
            >>> orchestrator.config.triggers.failure_threshold
            5
        """
        config = load_config(config_file=config_file, use_env=False, use_file=True)
        return cls(helpdesk=helpdesk, config=config)

    @property
    def helpdesk(self) -> str:
        """The helpdesk provider configured for this orchestrator."""
        return self._helpdesk

    @property
    def config(self) -> HandoffConfig:
        """The configuration for this orchestrator."""
        return self._config

    @property
    def triggers(self) -> TriggerConfig:
        """Shortcut to access trigger configuration (config.triggers)."""
        return self._config.triggers

    def should_handoff(
        self,
        conversation: list[Message],
        current_message: str,
    ) -> tuple[bool, Optional[TriggerResult]]:
        """Check if a conversation should be handed off to a human agent.

        This method evaluates the conversation history and current message
        to determine if a handoff to a human agent is needed.

        Args:
            conversation: List of Message objects representing the conversation history.
            current_message: The current message being evaluated.

        Returns:
            A tuple of (should_handoff, trigger_result) where:
            - should_handoff: True if handoff is recommended, False otherwise
            - trigger_result: TriggerResult with details if triggered, None otherwise

        Note:
            This is a stub implementation that always returns (False, None).
            Actual trigger detection will be implemented in Epic 2.

        Example:
            >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
            >>> messages = [Message(speaker="user", content="Hello")]
            >>> should_handoff, trigger = orchestrator.should_handoff(messages, "I want to talk to a human")
            >>> if should_handoff:
            ...     print(f"Handoff triggered: {trigger.reason}")
        """
        # Log the should_handoff call at DEBUG level
        message_preview = (
            current_message[:50] + "..." if len(current_message) > 50 else current_message
        )
        self._logger.debug(
            "Evaluating handoff decision",
            extra={
                "conversation_length": len(conversation),
                "message_preview": message_preview,
            },
        )

        # Stub implementation - actual trigger detection comes in Epic 2
        result = (False, None)

        # Log the decision at INFO level
        self._logger.info(
            "Handoff decision made",
            extra={
                "should_handoff": result[0],
                "trigger_type": result[1].trigger_type if result[1] else None,
                "confidence": result[1].confidence if result[1] else None,
                "conversation_length": len(conversation),
            },
        )

        return result

    def create_handoff(
        self,
        conversation: list[Message],
        metadata: Optional[dict[str, Any]] = None,
    ) -> HandoffResult:
        """Create a handoff to transfer the conversation to a human agent.

        This method packages the conversation context and initiates a handoff
        to the configured helpdesk system.

        Args:
            conversation: List of Message objects representing the conversation history.
            metadata: Optional dictionary of additional metadata to include with
                     the handoff (e.g., user_id, channel, custom fields).

        Returns:
            HandoffResult containing the outcome of the handoff attempt.

        Note:
            This is a stub implementation that returns a pending HandoffResult.
            Actual handoff execution will be implemented in Epic 3.

        Example:
            >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
            >>> messages = [Message(speaker="user", content="I need help")]
            >>> result = orchestrator.create_handoff(
            ...     messages,
            ...     metadata={"user_id": "123", "channel": "web"}
            ... )
            >>> print(f"Handoff status: {result.status}")
        """
        # Extract user_id from metadata for logging
        user_id = metadata.get("user_id") if metadata else None

        # Log the create_handoff call at INFO level
        self._logger.info(
            "Creating handoff",
            extra={
                "conversation_length": len(conversation),
                "user_id": user_id,
                "helpdesk": self._helpdesk,
                "metadata_keys": list(metadata.keys()) if metadata else [],
            },
        )

        # Package conversation history
        conversation_package = self._context_packager.package_conversation(conversation)

        # Initialize metadata if None
        if metadata is None:
            metadata = {}

        # Include packaged conversation in metadata
        metadata["conversation_package"] = conversation_package.model_dump()

        # Stub implementation - actual handoff execution comes in Epic 3
        result = HandoffResult(
            success=False,
            status=HandoffStatus.PENDING,
            error_message="Handoff execution not yet implemented",
            metadata=metadata,
        )

        # Log the result
        self._logger.info(
            "Handoff created",
            extra={
                "handoff_id": result.handoff_id,
                "status": result.status.value if result.status else None,
                "success": result.success,
                "helpdesk": self._helpdesk,
            },
        )

        return result
