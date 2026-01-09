"""Generic JSON integration for exporting context without external API calls."""

import uuid
from typing import Any, Optional

from handoffkit.context.adapters.json_adapter import JSONAdapter
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffResult,
    HandoffStatus,
)
from handoffkit.integrations.base import BaseIntegration
from handoffkit.utils.logging import get_logger

logger = get_logger("integrations.generic")


class GenericIntegration(BaseIntegration):
    """Integration that exports context as JSON without external API calls.

    This integration is designed for scenarios where you want to:
    - Export handoff context to your own custom system
    - Store handoff data locally for processing
    - Integrate with systems that accept JSON input
    - Test handoff flows without connecting to external services

    Unlike Zendesk or Intercom integrations, GenericIntegration does NOT
    make any external API calls. All data is stored in the HandoffResult.metadata.

    Example:
        >>> integration = GenericIntegration()
        >>> await integration.initialize()
        >>> result = await integration.create_ticket(context, decision)
        >>> json_content = result.metadata["json_content"]
    """

    @property
    def integration_name(self) -> str:
        """Return the name of this integration."""
        return "json"

    @property
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        return ["create_ticket", "export_json"]

    def __init__(
        self,
        pretty: bool = True,
        include_metadata: bool = True,
        exclude_empty_fields: bool = False,
    ) -> None:
        """Initialize GenericIntegration.

        Args:
            pretty: Whether to format JSON output with indentation.
            include_metadata: Whether to include metadata in output.
            exclude_empty_fields: Whether to exclude empty fields from output.
        """
        self._pretty = pretty
        self._include_metadata = include_metadata
        self._exclude_empty_fields = exclude_empty_fields
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the integration.

        For GenericIntegration, this is a no-op since no external
        API connection is needed.
        """
        logger.info("Initializing GenericIntegration (no external API)")
        self._initialized = True
        logger.info("GenericIntegration initialized successfully")

    async def create_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Export context as JSON without making external API calls.

        Creates a HandoffResult with the JSON-formatted context stored
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
            - metadata: Contains json_content, handoff_package, and decision info
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            f"Creating JSON export for conversation: {context.conversation_id}"
        )

        try:
            # Create adapter with configured options
            adapter = JSONAdapter(
                pretty=self._pretty,
                include_metadata=self._include_metadata,
                exclude_empty_fields=self._exclude_empty_fields,
            )

            # Generate JSON content
            json_content = adapter.convert(context)

            # Generate handoff package for structured access
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
            handoff_package = adapter.convert_to_handoff_package(
                context,
                trigger_type=trigger_type,
                priority=priority,
            )

            # Generate local handoff ID
            handoff_id = str(uuid.uuid4())

            logger.info(
                f"JSON export created successfully: {handoff_id}",
                extra={
                    "handoff_id": handoff_id,
                    "conversation_id": context.conversation_id,
                    "json_size_bytes": len(json_content.encode("utf-8")),
                },
            )

            return HandoffResult(
                success=True,
                handoff_id=handoff_id,
                status=HandoffStatus.PENDING,
                ticket_id=handoff_id,  # Use same ID since no external system
                ticket_url=None,  # No external URL
                metadata={
                    "json_content": json_content,
                    "handoff_package": handoff_package,
                    "export_format": "json",
                    "trigger_type": trigger_type,
                    "priority": priority,
                },
            )

        except Exception as e:
            error_msg = f"Failed to create JSON export: {e}"
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

        For GenericIntegration, this always returns an empty list since
        there is no external helpdesk system.

        Args:
            department: Optional department filter (ignored).

        Returns:
            Empty list (no agents in generic integration).
        """
        logger.debug("check_agent_availability called on GenericIntegration (no-op)")
        return []

    async def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str,
    ) -> bool:
        """Assign ticket to agent.

        For GenericIntegration, this always returns False since
        there is no external helpdesk system.

        Args:
            ticket_id: ID of the ticket (ignored).
            agent_id: ID of the agent (ignored).

        Returns:
            False (assignment not supported in generic integration).
        """
        logger.debug("assign_to_agent called on GenericIntegration (no-op)")
        return False

    async def get_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        """Get ticket status.

        For GenericIntegration, this returns a status indicating
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

        For GenericIntegration, this is a no-op.
        """
        self._initialized = False
        logger.debug("GenericIntegration closed")
