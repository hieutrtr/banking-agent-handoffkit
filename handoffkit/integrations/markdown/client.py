"""Markdown integration for exporting context without external API calls."""

import uuid
from typing import Any, Optional

from handoffkit.context.adapters.markdown_adapter import MarkdownAdapter
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffResult,
    HandoffStatus,
)
from handoffkit.integrations.base import BaseIntegration
from handoffkit.utils.logging import get_logger

logger = get_logger("integrations.markdown")


class MarkdownIntegration(BaseIntegration):
    """Integration that exports context as Markdown without external API calls.

    This integration is designed for scenarios where you want to:
    - Export handoff context in human-readable format
    - Copy/paste context into emails or tickets manually
    - Generate reports for review
    - Test handoff flows without connecting to external services

    Unlike Zendesk or Intercom integrations, MarkdownIntegration does NOT
    make any external API calls. All data is stored in the HandoffResult.metadata.

    Example:
        >>> integration = MarkdownIntegration()
        >>> await integration.initialize()
        >>> result = await integration.create_ticket(context, decision)
        >>> markdown_content = result.metadata["markdown_content"]
    """

    @property
    def integration_name(self) -> str:
        """Return the name of this integration."""
        return "markdown"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return ["create_ticket", "export_markdown"]

    def __init__(
        self,
        include_summary: bool = True,
        include_entities: bool = True,
        include_full_history: bool = False,
    ) -> None:
        """Initialize MarkdownIntegration.

        Args:
            include_summary: Whether to include AI-generated summary section.
            include_entities: Whether to include extracted entities section.
            include_full_history: Whether to include full message history.
                If False, only the last 10 messages are included.
        """
        self._include_summary = include_summary
        self._include_entities = include_entities
        self._include_full_history = include_full_history
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the integration.

        For MarkdownIntegration, this is a no-op since no external
        API connection is needed.
        """
        logger.info("Initializing MarkdownIntegration (no external API)")
        self._initialized = True
        logger.info("MarkdownIntegration initialized successfully")

    async def create_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Export context as Markdown without making external API calls.

        Creates a HandoffResult with the Markdown-formatted context stored
        in the metadata field. No external API is called.

        Args:
            context: The conversation context to export.
            decision: The handoff decision with trigger and priority info.

        Returns:
            HandoffResult with:
            - success=True
            - handoff_id: Locally generated UUID
            - ticket_id: Same as handoff_id (no external system)
            - ticket_url: None (no external URL)
            - metadata: Contains markdown_content and decision info
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            f"Creating Markdown export for conversation: {context.conversation_id}"
        )

        try:
            # Create adapter with configured options
            adapter = MarkdownAdapter(
                include_summary=self._include_summary,
                include_entities=self._include_entities,
                include_full_history=self._include_full_history,
            )

            # Generate Markdown content
            markdown_content = adapter.convert(context)

            # Generate local handoff ID
            handoff_id = str(uuid.uuid4())

            # Extract decision info
            trigger_type = None
            if decision.trigger_results:
                # Get trigger type from first trigger result
                first_trigger = decision.trigger_results[0]
                trigger_type = (
                    first_trigger.trigger_type.value
                    if first_trigger.trigger_type
                    else None
                )
            priority = decision.priority.value if decision.priority else None

            logger.info(
                f"Markdown export created successfully: {handoff_id}",
                extra={
                    "handoff_id": handoff_id,
                    "conversation_id": context.conversation_id,
                    "markdown_size_bytes": len(markdown_content.encode("utf-8")),
                },
            )

            return HandoffResult(
                success=True,
                handoff_id=handoff_id,
                status=HandoffStatus.PENDING,
                ticket_id=handoff_id,  # Use same ID since no external system
                ticket_url=None,  # No external URL
                metadata={
                    "markdown_content": markdown_content,
                    "export_format": "markdown",
                    "trigger_type": trigger_type,
                    "priority": priority,
                },
            )

        except Exception as e:
            error_msg = f"Failed to create Markdown export: {e}"
            logger.error(error_msg)
            return HandoffResult(
                success=False,
                status=HandoffStatus.FAILED,
                error_message=error_msg,
            )

    async def check_agent_availability(
        self,
        department: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Check agent availability.

        For MarkdownIntegration, this always returns an empty list since
        there is no external helpdesk system.

        Args:
            department: Optional department filter (ignored).

        Returns:
            Empty list (no agents in markdown integration).
        """
        logger.debug("check_agent_availability called on MarkdownIntegration (no-op)")
        return []

    async def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str,
    ) -> bool:
        """Assign ticket to agent.

        For MarkdownIntegration, this always returns False since
        there is no external helpdesk system.

        Args:
            ticket_id: ID of the ticket (ignored).
            agent_id: ID of the agent (ignored).

        Returns:
            False (assignment not supported in markdown integration).
        """
        logger.debug("assign_to_agent called on MarkdownIntegration (no-op)")
        return False

    async def get_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        """Get ticket status.

        For MarkdownIntegration, this returns a status indicating
        the ticket is stored locally.

        Args:
            ticket_id: ID of the ticket.

        Returns:
            Dictionary with local storage status.
        """
        return {
            "ticket_id": ticket_id,
            "status": "local",
            "message": "Ticket stored locally in HandoffResult.metadata",
        }

    async def close(self) -> None:
        """Clean up integration resources.

        For MarkdownIntegration, this is a no-op.
        """
        self._initialized = False
        logger.debug("MarkdownIntegration closed")
