"""Context preservation models for HandoffKit."""

import json
from datetime import datetime
from typing import Optional

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


class ConversationMetadata(BaseModel):
    """Metadata for handoff context.

    This model captures essential metadata about the conversation including
    user identification, channel information, and conversation analytics.

    Attributes:
        user_id: User identifier
        session_id: Session identifier (auto-generated UUID if not provided)
        channel: Communication channel (e.g., web, mobile, sms)
        attempted_solutions: AI suggestions and solutions that were tried
        failed_queries: User questions that weren't satisfactorily answered
        conversation_duration: Duration in seconds from first to last message
        timestamp: Timestamp of the last message in the conversation

    Example:
        >>> metadata = ConversationMetadata(
        ...     user_id="user123",
        ...     session_id="abc-def",
        ...     channel="web"
        ... )
        >>> metadata.to_dict()
        {'user_id': 'user123', 'session_id': 'abc-def', ...}
    """

    user_id: str = Field(description="User identifier")
    session_id: str = Field(description="Session identifier (auto-generated if missing)")
    channel: str = Field(description="Communication channel (web, mobile, sms, etc.)")
    attempted_solutions: list[str] = Field(
        default_factory=list,
        description="AI suggestions and solutions attempted",
    )
    failed_queries: list[str] = Field(
        default_factory=list,
        description="User questions that weren't satisfactorily answered",
    )
    conversation_duration: int = Field(
        default=0,
        description="Duration in seconds from first to last message",
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp of last message",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields serialized to JSON-compatible types

        Example:
            >>> metadata.to_dict()
            {'user_id': 'user123', ...}
        """
        return self.model_dump(mode="json")
