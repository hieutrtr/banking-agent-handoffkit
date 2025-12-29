"""Base class for handoff triggers."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from handoffkit.core.types import Message, TriggerResult


class BaseTrigger(ABC):
    """Abstract base class for all handoff triggers."""

    @property
    @abstractmethod
    def trigger_name(self) -> str:
        """Return the name of this trigger."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate if this trigger should fire.

        Args:
            message: The current message to evaluate.
            history: Previous messages in the conversation.
            context: Additional context for evaluation.

        Returns:
            TriggerResult indicating if triggered and why.
        """
        pass

    async def initialize(self) -> None:
        """Initialize the trigger. Override for setup logic."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources. Override for teardown logic."""
        pass
