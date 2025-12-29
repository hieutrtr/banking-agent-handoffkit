"""Markdown format adapter for context export."""

from handoffkit.context.adapters.base import BaseAdapter
from handoffkit.core.types import ConversationContext


class MarkdownAdapter(BaseAdapter):
    """Converts conversation context to Markdown format."""

    @property
    def adapter_name(self) -> str:
        return "markdown"

    @property
    def output_format(self) -> str:
        return "markdown"

    def __init__(
        self,
        include_summary: bool = True,
        include_entities: bool = True,
        include_full_history: bool = False,
    ) -> None:
        """Initialize Markdown adapter.

        Args:
            include_summary: Include AI-generated summary.
            include_entities: Include extracted entities section.
            include_full_history: Include full message history.
        """
        self._include_summary = include_summary
        self._include_entities = include_entities
        self._include_full_history = include_full_history

    def convert(self, context: ConversationContext) -> str:
        """Convert context to Markdown string.

        Args:
            context: The conversation context.

        Returns:
            Markdown-formatted string.
        """
        raise NotImplementedError("MarkdownAdapter conversion pending")
