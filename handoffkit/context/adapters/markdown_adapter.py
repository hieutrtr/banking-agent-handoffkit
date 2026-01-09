"""Markdown format adapter for context export."""

from typing import Any

from handoffkit.context.adapters.base import BaseAdapter
from handoffkit.core.types import ConversationContext


class MarkdownAdapter(BaseAdapter):
    """Converts conversation context to Markdown format.

    This adapter generates human-readable markdown suitable for pasting
    into tickets, emails, or other documentation systems.

    Features:
    - Configurable sections (summary, entities, full history)
    - Speaker-labeled message history with timestamps
    - Session metadata display
    - Truncates to last max_messages messages by default (configurable via include_full_history)

    Example:
        >>> from handoffkit.core.types import ConversationContext, Message, MessageSpeaker
        >>> from datetime import datetime, timezone
        >>>
        >>> # Create a simple context
        >>> context = ConversationContext(
        ...     conversation_id="conv-123",
        ...     messages=[
        ...         Message(
        ...             speaker=MessageSpeaker.USER,
        ...             content="I need help with my account",
        ...             timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        ...         )
        ...     ],
        ...     metadata={"user_id": "user-456"}
        ... )
        >>>
        >>> # Convert to markdown
        >>> adapter = MarkdownAdapter(include_summary=True, include_entities=True)
        >>> markdown = adapter.convert(context)
        >>> print(markdown)
        # Handoff Context: conv-123
        **Created:** 2024-01-15T10:00:00+00:00

        ## Conversation History
        **User** (10:00:00): I need help with my account

        ## Session Info
        - **User ID:** user-456
        - **Session ID:** Unknown
        - **Channel:** Unknown
    """

    @property
    def adapter_name(self) -> str:
        """Return the name of this adapter."""
        return "markdown"

    @property
    def output_format(self) -> str:
        """Return the output format."""
        return "markdown"

    def __init__(
        self,
        include_summary: bool = True,
        include_entities: bool = True,
        include_full_history: bool = False,
        max_messages: int = 10,
    ) -> None:
        """Initialize Markdown adapter.

        Args:
            include_summary: Include AI-generated summary section.
            include_entities: Include extracted entities section.
            include_full_history: Include full message history. If False,
                only the last max_messages messages are included.
            max_messages: Maximum number of messages to show when not showing
                full history. Defaults to 10.
        """
        self._include_summary = include_summary
        self._include_entities = include_entities
        self._include_full_history = include_full_history
        self._max_messages = max_messages

    def validate_context(self, context: ConversationContext) -> bool:
        """Validate context before conversion.

        Args:
            context: Context to validate.

        Returns:
            True if context is valid for this adapter.

        Raises:
            ValueError: If context is invalid.
        """
        if not super().validate_context(context):
            return False

        # Additional validation for markdown adapter
        if context.messages is None:
            raise ValueError("Context messages cannot be None")

        if not isinstance(context.messages, list):
            raise ValueError("Context messages must be a list")

        return True

    def convert(self, context: ConversationContext) -> str:
        """Convert context to Markdown string.

        Generates a human-readable markdown document with the following sections:
        - Header with conversation ID and timestamp
        - Summary (if enabled and available)
        - Key Information / Entities (if enabled and available)
        - Conversation History (with speaker labels and timestamps)
        - Session Info (user_id, session_id, channel)

        Args:
            context: The conversation context to convert.

        Returns:
            Markdown-formatted string suitable for pasting into tickets/emails.

        Raises:
            ValueError: If context validation fails.
        """
        # Validate context before processing
        self.validate_context(context)

        sections: list[str] = []

        # Header with conversation ID and timestamp
        sections.append(f"# Handoff Context: {context.conversation_id}")
        sections.append(f"**Created:** {context.created_at.isoformat()}")
        sections.append("")

        # Summary section (from metadata if available)
        if self._include_summary:
            summary = context.metadata.get("conversation_summary")
            if summary:
                sections.append("## Summary")
                if isinstance(summary, dict):
                    summary_text = summary.get("summary_text", "No summary available")
                    sections.append(summary_text)
                else:
                    sections.append(str(summary))
                sections.append("")

        # Entities section
        if self._include_entities and context.entities:
            sections.append("## Key Information")
            for entity_type, values in context.entities.items():
                if isinstance(values, list):
                    for value in values:
                        sections.append(
                            f"- **{self._format_entity_type(entity_type)}:** {self._format_entity_value(value)}"
                        )
                else:
                    sections.append(
                        f"- **{self._format_entity_type(entity_type)}:** {self._format_entity_value(values)}"
                    )
            sections.append("")

        # Conversation History section
        sections.append("## Conversation History")
        messages = context.messages
        if not self._include_full_history and len(messages) > self._max_messages:
            # Truncate to last max_messages messages
            messages = messages[-self._max_messages:]
            sections.append(f"*Showing last {self._max_messages} of {len(context.messages)} messages*")
            sections.append("")

        if messages:
            for msg in messages:
                speaker = "User" if msg.speaker.value == "user" else "AI"
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                # Escape any markdown in content
                content = msg.content.replace("\n", " ").strip()
                escaped_content = self._escape_markdown(content)
                sections.append(f"**{speaker}** ({timestamp}): {escaped_content}")
        else:
            sections.append("*No messages in conversation*")
        sections.append("")

        # Session Info / Metadata section
        sections.append("## Session Info")
        sections.append(f"- **User ID:** {context.user_id or 'Unknown'}")
        sections.append(f"- **Session ID:** {context.session_id or 'Unknown'}")
        sections.append(f"- **Channel:** {context.channel or 'Unknown'}")

        # Add conversation duration if available in metadata
        duration = context.metadata.get("conversation_duration")
        if duration is not None:
            sections.append(f"- **Duration:** {duration} seconds")

        return "\n".join(sections)

    def _format_entity_type(self, entity_type: str) -> str:
        """Format entity type for display.

        Converts snake_case to Title Case.

        Args:
            entity_type: The entity type string (e.g., 'account_number').

        Returns:
            Formatted string (e.g., 'Account Number').
        """
        return entity_type.replace("_", " ").title()

    def _escape_markdown(self, text: str) -> str:
        """Escape markdown special characters in text.

        Args:
            text: The text to escape.

        Returns:
            Text with markdown special characters escaped.
        """
        # Escape markdown special characters
        markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '>', '|']
        for char in markdown_chars:
            text = text.replace(char, f"\\{char}")
        return text

    def _format_entity_value(self, value: Any) -> str:
        """Format entity value for display.

        Handles various value types including dicts with 'masked_value' keys.

        Args:
            value: The entity value to format.

        Returns:
            String representation of the value.
        """
        if isinstance(value, dict):
            # Check for masked value (from ExtractedEntity)
            if "masked_value" in value and value["masked_value"]:
                return str(value["masked_value"])
            elif "original_value" in value:
                return str(value["original_value"])
            else:
                return str(value)
        return str(value)
