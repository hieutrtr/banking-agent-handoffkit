"""Context preservation models for HandoffKit."""

import json

from pydantic import BaseModel, Field


class ConversationPackage(BaseModel):
    """Packaged conversation history for handoff.

    This model represents a formatted and size-limited conversation history
    ready for handoff to human agents.

    Attributes:
        messages: Formatted message history as JSON-serializable dicts
        message_count: Number of messages included in the package
        total_messages: Total messages in original conversation
        truncated: Whether messages were truncated due to limits
        size_bytes: Total JSON size in bytes

    Example:
        >>> package = ConversationPackage(
        ...     messages=[{"speaker": "user", "content": "Hello"}],
        ...     message_count=1,
        ...     total_messages=1,
        ...     truncated=False,
        ...     size_bytes=100
        ... )
        >>> package.to_json()
        '{\n  "messages": [...],\n  ...\n}'
    """

    messages: list[dict] = Field(description="Formatted message history")
    message_count: int = Field(description="Number of messages included")
    total_messages: int = Field(description="Total messages in conversation")
    truncated: bool = Field(description="Whether messages were truncated")
    size_bytes: int = Field(description="Total JSON size in bytes")

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            Valid JSON string representation with 2-space indentation

        Example:
            >>> package.to_json()
            '{\n  "messages": [...],\n  "message_count": 1,\n  ...\n}'
        """
        return json.dumps(self.model_dump(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationPackage":
        """Create from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            ConversationPackage instance

        Raises:
            json.JSONDecodeError: If json_str is invalid JSON
            ValidationError: If JSON doesn't match ConversationPackage schema

        Example:
            >>> json_str = '{"messages": [], "message_count": 0, ...}'
            >>> package = ConversationPackage.from_json(json_str)
        """
        data = json.loads(json_str)
        return cls(**data)
