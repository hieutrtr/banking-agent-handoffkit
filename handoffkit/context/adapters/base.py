"""Base adapter for context format conversion."""

from abc import ABC, abstractmethod
from typing import Any

from handoffkit.core.types import ConversationContext


class BaseAdapter(ABC):
    """Abstract base class for context format adapters."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Return the name of this adapter."""
        pass

    @property
    @abstractmethod
    def output_format(self) -> str:
        """Return the output format (e.g., 'json', 'markdown', 'zendesk')."""
        pass

    @abstractmethod
    def convert(self, context: ConversationContext) -> Any:
        """Convert context to target format.

        Args:
            context: The conversation context to convert.

        Returns:
            Context in the target format.
        """
        pass

    def validate_context(self, context: ConversationContext) -> bool:
        """Validate context before conversion.

        Args:
            context: Context to validate.

        Returns:
            True if context is valid for this adapter.
        """
        return context.conversation_id is not None
