"""Base class for helpdesk integrations."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from handoffkit.core.types import ConversationContext, HandoffDecision, HandoffResult


class BaseIntegration(ABC):
    """Abstract base class for helpdesk system integrations."""

    @property
    @abstractmethod
    def integration_name(self) -> str:
        """Return the name of this integration."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> list[str]:
        """Return list of supported features."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the integration (authenticate, validate config)."""
        pass

    @abstractmethod
    async def create_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Create a support ticket in the helpdesk system.

        Args:
            context: Packaged conversation context.
            decision: Handoff decision with priority.

        Returns:
            HandoffResult with ticket details.
        """
        pass

    @abstractmethod
    async def check_agent_availability(
        self,
        department: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Check available agents in the helpdesk.

        Args:
            department: Optional department filter.

        Returns:
            List of available agent info.
        """
        pass

    @abstractmethod
    async def assign_to_agent(
        self,
        ticket_id: str,
        agent_id: str,
    ) -> bool:
        """Assign a ticket to a specific agent.

        Args:
            ticket_id: ID of the ticket.
            agent_id: ID of the agent.

        Returns:
            True if assignment succeeded.
        """
        pass

    async def get_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        """Get the current status of a ticket.

        Args:
            ticket_id: ID of the ticket.

        Returns:
            Ticket status information.
        """
        raise NotImplementedError("Ticket status not implemented")

    async def close(self) -> None:
        """Clean up integration resources."""
        pass
