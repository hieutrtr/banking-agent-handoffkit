"""Routing strategies for agent selection."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseStrategy(ABC):
    """Abstract base class for routing strategies."""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the name of this strategy."""
        pass

    @abstractmethod
    def select_agent(
        self,
        available_agents: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Select an agent from available options.

        Args:
            available_agents: List of available agents.
            context: Additional context for selection.

        Returns:
            Selected agent or None if no suitable agent.
        """
        pass


class RoundRobinStrategy(BaseStrategy):
    """Simple round-robin agent selection."""

    @property
    def strategy_name(self) -> str:
        return "round_robin"

    def __init__(self) -> None:
        """Initialize round-robin strategy."""
        self._last_index = -1

    def select_agent(
        self,
        available_agents: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Select next agent in rotation."""
        if not available_agents:
            return None

        self._last_index = (self._last_index + 1) % len(available_agents)
        return available_agents[self._last_index]


class LeastBusyStrategy(BaseStrategy):
    """Select agent with fewest active conversations."""

    @property
    def strategy_name(self) -> str:
        return "least_busy"

    def select_agent(
        self,
        available_agents: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Select agent with lowest active conversation count."""
        raise NotImplementedError("LeastBusyStrategy selection pending")


class SkillBasedStrategy(BaseStrategy):
    """Select agent based on required skills matching."""

    @property
    def strategy_name(self) -> str:
        return "skill_based"

    def select_agent(
        self,
        available_agents: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Select agent with best skill match."""
        raise NotImplementedError("SkillBasedStrategy selection pending")
