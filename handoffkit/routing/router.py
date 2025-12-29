"""Agent router for intelligent handoff routing."""

from typing import Any, Optional

from handoffkit.core.config import RoutingConfig
from handoffkit.core.types import ConversationContext, HandoffDecision, HandoffResult
from handoffkit.routing.strategies import BaseStrategy, RoundRobinStrategy


class AgentRouter:
    """Routes handoffs to available human agents.

    Features:
    - Real-time agent availability checking (30s cache TTL)
    - Multiple routing strategies (round-robin, least-busy, skill-based)
    - Fallback ticket creation when no agents available
    - Department/skill matching
    """

    def __init__(self, config: Optional[RoutingConfig] = None) -> None:
        """Initialize agent router.

        Args:
            config: Routing configuration.
        """
        self._config = config or RoutingConfig()
        self._strategy = self._create_strategy(self._config.strategy)
        self._availability_cache: dict[str, Any] = {}
        self._cache_ttl = self._config.availability_cache_ttl

    def _create_strategy(self, strategy_name: str) -> BaseStrategy:
        """Create routing strategy by name."""
        strategies = {
            "round_robin": RoundRobinStrategy,
            # Other strategies added in future stories
        }
        strategy_class = strategies.get(strategy_name, RoundRobinStrategy)
        return strategy_class()

    async def route(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Route handoff to an agent or create fallback ticket.

        Args:
            context: Packaged conversation context.
            decision: Handoff decision with priority and department.

        Returns:
            HandoffResult with routing outcome.
        """
        raise NotImplementedError("AgentRouter routing pending")

    async def check_availability(
        self,
        department: Optional[str] = None,
        skills: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Check agent availability.

        Args:
            department: Filter by department.
            skills: Required skills.

        Returns:
            List of available agents.
        """
        raise NotImplementedError("AgentRouter availability check pending")

    async def create_fallback_ticket(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
    ) -> HandoffResult:
        """Create fallback ticket when no agents available.

        Args:
            context: Conversation context.
            decision: Handoff decision.

        Returns:
            HandoffResult with ticket information.
        """
        raise NotImplementedError("AgentRouter fallback ticket pending")
