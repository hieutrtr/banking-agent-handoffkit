"""JSON format adapter for context export."""

import json
from typing import Any, Optional

from handoffkit.context.adapters.base import BaseAdapter
from handoffkit.core.types import ConversationContext


class JSONAdapter(BaseAdapter):
    """Converts conversation context to JSON format.

    This adapter generates a standardized JSON structure suitable for
    integration with any system that accepts JSON input.

    Features:
    - Standardized structure with conversation, metadata, summary, entities sections
    - Optional pretty-printing with indentation
    - Optional metadata inclusion/exclusion
    - Optional filtering of empty fields
    - HandoffResult-compatible output via convert_to_handoff_package()

    Example:
        >>> from handoffkit.core.types import ConversationContext, Message, MessageSpeaker
        >>> from datetime import datetime, timezone
        >>>
        >>> # Create a simple context
        >>> context = ConversationContext(
        ...     conversation_id="conv-123",
        ...     user_id="user-456",
        ...     messages=[
        ...         Message(
        ...             speaker=MessageSpeaker.USER,
        ...             content="I need help",
        ...             timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        ...         )
        ...     ]
        ... )
        >>>
        >>> # Convert to JSON
        >>> adapter = JSONAdapter(pretty=True, include_metadata=True)
        >>> json_str = adapter.convert(context)
        >>> print(json_str)
        {
          "conversation_id": "conv-123",
          "user_id": "user-456",
          "messages": [
            {
              "speaker": "user",
              "content": "I need help",
              "timestamp": "2024-01-15T10:00:00+00:00"
            }
          ]
        }
    """

    @property
    def adapter_name(self) -> str:
        """Return the name of this adapter."""
        return "json"

    @property
    def output_format(self) -> str:
        """Return the output format."""
        return "json"

    def __init__(
        self,
        pretty: bool = True,
        include_metadata: bool = True,
        exclude_empty_fields: bool = False,
    ) -> None:
        """Initialize JSON adapter.

        Args:
            pretty: Whether to format output with indentation.
            include_metadata: Whether to include metadata fields.
            exclude_empty_fields: Whether to exclude empty lists/dicts/None values.
        """
        self._pretty = pretty
        self._include_metadata = include_metadata
        self._exclude_empty_fields = exclude_empty_fields

    def convert(self, context: ConversationContext) -> str:
        """Convert context to JSON string.

        Generates a standardized JSON structure with:
        - conversation_id, user_id, session_id, channel, created_at
        - messages array with speaker, content, timestamp
        - entities dictionary
        - metadata dictionary (if include_metadata=True)

        Args:
            context: The conversation context.

        Returns:
            JSON-formatted string.
        """
        data = self._build_standardized_structure(context)

        if self._pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def convert_to_dict(self, context: ConversationContext) -> dict[str, Any]:
        """Convert context to dictionary.

        Args:
            context: The conversation context.

        Returns:
            Dictionary representation with standardized structure.
        """
        return self._build_standardized_structure(context)

    def convert_to_handoff_package(
        self,
        context: ConversationContext,
        trigger_type: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> dict[str, Any]:
        """Convert context to HandoffResult-compatible dictionary.

        This method produces a structure that can be directly stored in
        HandoffResult.metadata for use with GenericIntegration.

        Args:
            context: The conversation context.
            trigger_type: Optional trigger type that initiated the handoff.
            priority: Optional priority level for the handoff.

        Returns:
            Dictionary with:
            - conversation: Standardized conversation data
            - summary: Conversation summary (if available)
            - entities: Extracted entities
            - metadata: Session and context metadata
            - handoff_info: Trigger and priority information
        """
        base_data = self._build_standardized_structure(context)

        # Extract summary from metadata if present
        summary = context.metadata.get("conversation_summary")
        if isinstance(summary, dict):
            summary_text = summary.get("summary_text", "")
        elif summary:
            summary_text = str(summary)
        else:
            summary_text = None

        # Build handoff package
        package: dict[str, Any] = {
            "conversation": {
                "id": base_data["conversation_id"],
                "user_id": base_data.get("user_id"),
                "session_id": base_data.get("session_id"),
                "channel": base_data.get("channel"),
                "created_at": base_data.get("created_at"),
                "messages": base_data.get("messages", []),
            },
            "summary": summary_text,
            "entities": base_data.get("entities", {}),
            "metadata": base_data.get("metadata", {}),
            "handoff_info": {
                "trigger_type": trigger_type,
                "priority": priority,
            },
        }

        if self._exclude_empty_fields:
            package = self._remove_empty_fields(package)

        return package

    def _build_standardized_structure(
        self, context: ConversationContext
    ) -> dict[str, Any]:
        """Build standardized JSON structure from context.

        Args:
            context: The conversation context.

        Returns:
            Dictionary with standardized structure.
        """
        data = context.model_dump(mode="json")

        if not self._include_metadata:
            data.pop("metadata", None)

        if self._exclude_empty_fields:
            data = self._remove_empty_fields(data)

        return data

    def _remove_empty_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove empty fields from dictionary recursively.

        Args:
            data: Dictionary to clean.

        Returns:
            Dictionary with empty fields removed.
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned = self._remove_empty_fields(value)
                if cleaned:  # Only include non-empty dicts
                    result[key] = cleaned
            elif isinstance(value, list):
                if value:  # Only include non-empty lists
                    result[key] = value
            elif value is not None:
                result[key] = value
        return result
