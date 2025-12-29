"""JSON format adapter for context export."""

import json
from typing import Any

from handoffkit.context.adapters.base import BaseAdapter
from handoffkit.core.types import ConversationContext


class JSONAdapter(BaseAdapter):
    """Converts conversation context to JSON format."""

    @property
    def adapter_name(self) -> str:
        return "json"

    @property
    def output_format(self) -> str:
        return "json"

    def __init__(self, pretty: bool = True, include_metadata: bool = True) -> None:
        """Initialize JSON adapter.

        Args:
            pretty: Whether to format output with indentation.
            include_metadata: Whether to include metadata fields.
        """
        self._pretty = pretty
        self._include_metadata = include_metadata

    def convert(self, context: ConversationContext) -> str:
        """Convert context to JSON string.

        Args:
            context: The conversation context.

        Returns:
            JSON-formatted string.
        """
        data = context.model_dump(mode="json")
        if not self._include_metadata:
            data.pop("metadata", None)

        if self._pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def convert_to_dict(self, context: ConversationContext) -> dict[str, Any]:
        """Convert context to dictionary.

        Args:
            context: The conversation context.

        Returns:
            Dictionary representation.
        """
        return context.model_dump(mode="json")
