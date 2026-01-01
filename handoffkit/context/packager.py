"""Context packaging for handoff operations."""

import json

from handoffkit.context.models import ConversationPackage
from handoffkit.core.types import Message
from handoffkit.utils.logging import get_logger

logger = get_logger("context.packager")


class ConversationPackager:
    """Package conversation history for handoff.

    This class handles conversation message history packaging with
    configurable message count and size limits.

    Features:
    - Limits to most recent N messages (default 100)
    - Caps total size at N KB (default 50KB)
    - Converts messages to JSON-serializable format
    - Includes timestamp, speaker, content, and AI confidence
    - Handles UTF-8 encoding for size calculation

    Example:
        >>> from handoffkit.context.packager import ConversationPackager
        >>> from handoffkit.core.types import Message
        >>> packager = ConversationPackager(max_messages=100, max_size_kb=50)
        >>> messages = [Message(speaker="user", content="Hello")]
        >>> package = packager.package_conversation(messages)
        >>> package.message_count
        1
    """

    def __init__(
        self,
        max_messages: int = 100,
        max_size_kb: int = 50,
    ) -> None:
        """Initialize conversation packager.

        Args:
            max_messages: Maximum number of messages to include (default 100).
                Must be a positive integer.
            max_size_kb: Maximum total size in kilobytes (default 50).
                Must be a positive integer.

        Raises:
            ValueError: If max_messages or max_size_kb are not positive integers.

        Example:
            >>> packager = ConversationPackager(max_messages=50, max_size_kb=25)
        """
        # Validate max_messages
        if not isinstance(max_messages, int) or max_messages <= 0:
            raise ValueError(
                f"max_messages must be a positive integer, got {max_messages!r}"
            )
        # Validate max_size_kb
        if not isinstance(max_size_kb, int) or max_size_kb <= 0:
            raise ValueError(
                f"max_size_kb must be a positive integer, got {max_size_kb!r}"
            )

        self._max_messages = max_messages
        self._max_size_kb = max_size_kb
        self._max_size_bytes = max_size_kb * 1024

    def package_conversation(
        self,
        messages: list[Message],
    ) -> ConversationPackage:
        """Package conversation history with size and count limits.

        This method:
        1. Limits to most recent max_messages (default 100)
        2. Converts Message objects to JSON-serializable dicts
        3. Calculates total JSON size in bytes (UTF-8)
        4. Progressively removes oldest messages if size exceeds limit
        5. Returns ConversationPackage with metadata

        Args:
            messages: List of Message objects to package

        Returns:
            ConversationPackage with formatted messages and metadata

        Example:
            >>> messages = [Message(speaker="user", content="Hello")]
            >>> package = packager.package_conversation(messages)
            >>> package.message_count
            1
        """
        # Log packaging start
        logger.info(
            "Starting conversation packaging",
            extra={
                "input_message_count": len(messages),
                "max_messages": self._max_messages,
                "max_size_kb": self._max_size_kb,
            },
        )

        if not messages:
            return ConversationPackage(
                messages=[],
                message_count=0,
                total_messages=0,
                truncated=False,
                size_bytes=0,
            )

        total_messages = len(messages)

        # Limit to most recent max_messages
        recent_messages = messages[-self._max_messages :]

        # Convert to JSON-serializable format
        formatted_messages = [
            {
                "speaker": msg.speaker.value,  # Convert enum to string
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),  # ISO 8601 format
                "ai_confidence": msg.metadata.get("ai_confidence"),
            }
            for msg in recent_messages
        ]

        # Check size and truncate if needed
        json_data = json.dumps(formatted_messages)
        size_bytes = len(json_data.encode("utf-8"))

        # Progressively remove oldest messages if over size limit
        while size_bytes > self._max_size_bytes and len(formatted_messages) > 1:
            formatted_messages.pop(0)  # Remove oldest
            json_data = json.dumps(formatted_messages)
            size_bytes = len(json_data.encode("utf-8"))

        truncated = len(formatted_messages) < total_messages

        if truncated:
            logger.warning(
                f"Conversation truncated: {total_messages} messages → "
                f"{len(formatted_messages)} messages, size: {size_bytes} bytes"
            )

        result = ConversationPackage(
            messages=formatted_messages,
            message_count=len(formatted_messages),
            total_messages=total_messages,
            truncated=truncated,
            size_bytes=size_bytes,
        )

        # Log packaging completion
        logger.info(
            "Conversation packaging completed",
            extra={
                "message_count": result.message_count,
                "total_messages": result.total_messages,
                "truncated": result.truncated,
                "size_bytes": result.size_bytes,
            },
        )

        return result
