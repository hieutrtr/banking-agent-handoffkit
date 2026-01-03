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

from typing import Any, Optional

from handoffkit.core.config import HandoffConfig, TriggerConfig
from handoffkit.core.config_loader import ConfigLoader, load_config
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    TriggerResult,
)
from handoffkit.integrations.base import BaseIntegration
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

        # Initialize context preservation components
        # Late import to avoid circular dependency
        from handoffkit.context.packager import ConversationPackager
        from handoffkit.context.metadata import MetadataCollector
        from handoffkit.context.entity_extractor import EntityExtractor
        from handoffkit.context.summarizer import ConversationSummarizer

        self._context_packager = ConversationPackager(
            max_messages=self._config.max_context_messages,
            max_size_kb=self._config.max_context_size_kb,
        )

        self._metadata_collector = MetadataCollector()
        self._entity_extractor = EntityExtractor()
        self._summarizer = ConversationSummarizer(
            max_words=self._config.summary_max_words
        )

        # Helpdesk integration (lazy initialized)
        self._integration: Optional[BaseIntegration] = None

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

    async def _get_integration(self) -> Optional[BaseIntegration]:
        """Lazy initialize and return the helpdesk integration.

        Returns:
            The initialized integration, or None if configuration is missing.
        """
        if self._integration is not None:
            return self._integration

        if self._helpdesk == "zendesk":
            # Import here to avoid circular dependency
            from handoffkit.integrations.zendesk import ZendeskConfig, ZendeskIntegration

            # Try to get config from IntegrationConfig.extra or environment
            extra = self._config.integration.extra
            if extra.get("subdomain") and extra.get("email") and extra.get("api_token"):
                config = ZendeskConfig(
                    subdomain=extra["subdomain"],
                    email=extra["email"],
                    api_token=extra["api_token"],
                )
            else:
                # Fall back to environment variables
                config = ZendeskConfig.from_env()

            if config is None:
                self._logger.warning(
                    "Zendesk configuration not found. Set ZENDESK_SUBDOMAIN, "
                    "ZENDESK_EMAIL, ZENDESK_API_TOKEN environment variables or "
                    "provide config via integration.extra."
                )
                return None

            self._integration = ZendeskIntegration(**config.to_integration_kwargs())
            await self._integration.initialize()
            self._logger.info("Zendesk integration initialized")

        elif self._helpdesk == "intercom":
            # Placeholder for Intercom integration
            self._logger.warning("Intercom integration not yet implemented")
            return None

        elif self._helpdesk == "custom":
            # Custom integrations must be set explicitly via set_integration()
            self._logger.debug("Custom helpdesk requires explicit integration setup")
            return None

        return self._integration

    def set_integration(self, integration: BaseIntegration) -> None:
        """Set a custom helpdesk integration.

        Use this for custom integrations or testing.

        Args:
            integration: The integration instance to use.
        """
        self._integration = integration
        self._logger.debug(f"Custom integration set: {integration.integration_name}")

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

    async def create_handoff(
        self,
        conversation: list[Message],
        metadata: Optional[dict[str, Any]] = None,
        trigger_result: Optional[TriggerResult] = None,
    ) -> HandoffResult:
        """Create a handoff to transfer the conversation to a human agent.

        This method packages the conversation context and initiates a handoff
        to the configured helpdesk system.

        Args:
            conversation: List of Message objects representing the conversation history.
            metadata: Optional dictionary of additional metadata to include with
                     the handoff (e.g., user_id, channel, custom fields).
            trigger_result: Optional TriggerResult from should_handoff() to include
                           in the handoff decision.

        Returns:
            HandoffResult containing the outcome of the handoff attempt.

        Example:
            >>> orchestrator = HandoffOrchestrator(helpdesk="zendesk")
            >>> messages = [Message(speaker="user", content="I need help")]
            >>> result = await orchestrator.create_handoff(
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

        # Collect metadata
        conversation_metadata = self._metadata_collector.collect_metadata(
            conversation, metadata or {}
        )

        # Extract entities from conversation
        extracted_entities = self._entity_extractor.extract_entities(conversation)

        # Generate conversation summary
        conversation_summary = self._summarizer.summarize(conversation)

        # Initialize metadata if None
        if metadata is None:
            metadata = {}

        # Include packaged conversation, metadata, extracted entities, and summary
        metadata["conversation_package"] = conversation_package.model_dump()
        metadata["conversation_metadata"] = conversation_metadata.to_dict()
        metadata["extracted_entities"] = [e.to_dict() for e in extracted_entities]
        metadata["conversation_summary"] = conversation_summary.to_dict()

        # Build ConversationContext for the integration
        # Get or generate conversation_id
        conversation_id = metadata.get(
            "conversation_id",
            conversation_metadata.session_id  # Use session_id as fallback
        )
        context = ConversationContext(
            conversation_id=conversation_id,
            messages=conversation,
            metadata=metadata,
            entities={e.entity_type.value: e.masked_value for e in extracted_entities},
            user_id=metadata.get("user_id"),
            session_id=metadata.get("session_id"),
            channel=metadata.get("channel"),
        )

        # Build HandoffDecision
        trigger_results = [trigger_result] if trigger_result else []
        priority = HandoffPriority.MEDIUM
        if trigger_result:
            # Map trigger confidence to priority
            if trigger_result.confidence >= 0.9:
                priority = HandoffPriority.URGENT
            elif trigger_result.confidence >= 0.7:
                priority = HandoffPriority.HIGH
            elif trigger_result.confidence >= 0.5:
                priority = HandoffPriority.MEDIUM
            else:
                priority = HandoffPriority.LOW

        decision = HandoffDecision(
            should_handoff=True,
            priority=priority,
            trigger_results=trigger_results,
            reasoning="Handoff initiated via create_handoff()",
        )

        # Try to use the configured integration
        integration = await self._get_integration()
        if integration is not None:
            try:
                result = await integration.create_ticket(context, decision)
            except Exception as e:
                self._logger.error(f"Integration error: {e}")
                result = HandoffResult(
                    success=False,
                    status=HandoffStatus.PENDING,
                    error_message=f"Integration error: {e}",
                    metadata=metadata,
                )
        else:
            # No integration available - return pending result
            result = HandoffResult(
                success=False,
                status=HandoffStatus.PENDING,
                error_message=f"No {self._helpdesk} integration configured",
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
