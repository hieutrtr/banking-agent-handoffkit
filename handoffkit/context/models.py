"""Context preservation models for HandoffKit."""

import json
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of extractable entities from conversations.

    Attributes:
        ACCOUNT_NUMBER: Bank account or reference numbers
        CURRENCY: Monetary amounts with currency
        DATE: Absolute or relative dates
        EMAIL: Email addresses
        PHONE: Phone numbers
        NAME: Person names

    Example:
        >>> EntityType.ACCOUNT_NUMBER.value
        'account_number'
    """

    ACCOUNT_NUMBER = "account_number"
    CURRENCY = "currency"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"


class ExtractedEntity(BaseModel):
    """Extracted entity from conversation.

    Represents a single entity (account number, currency, date, etc.)
    extracted from a conversation message with position and masking info.

    Attributes:
        entity_type: Type of entity (from EntityType enum)
        original_value: Original text as found in the message
        masked_value: Masked value for PII protection (e.g., ****5678)
        normalized_value: Parsed/normalized value (e.g., ISO date, float amount)
        message_index: Index of the message containing this entity
        start_pos: Start position of entity in the message
        end_pos: End position of entity in the message

    Example:
        >>> entity = ExtractedEntity(
        ...     entity_type=EntityType.ACCOUNT_NUMBER,
        ...     original_value="12345678",
        ...     masked_value="****5678",
        ...     normalized_value=None,
        ...     message_index=0,
        ...     start_pos=15,
        ...     end_pos=23
        ... )
        >>> entity.to_dict()
        {'entity_type': 'account_number', ...}
    """

    entity_type: EntityType = Field(description="Type of entity")
    original_value: str = Field(description="Original text as found")
    masked_value: Optional[str] = Field(None, description="Masked value for PII")
    normalized_value: Optional[str] = Field(None, description="Normalized/parsed value")
    message_index: int = Field(description="Index of message containing entity")
    start_pos: int = Field(description="Start position in message")
    end_pos: int = Field(description="End position in message")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields serialized to JSON-compatible types

        Example:
            >>> entity.to_dict()
            {'entity_type': 'account_number', 'original_value': '12345678', ...}
        """
        return self.model_dump(mode="json")


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


class ConversationSummary(BaseModel):
    """Summary of conversation for handoff context.

    This model captures a concise AI-generated summary of the conversation
    including the primary issue, attempted solutions, and current status.

    Attributes:
        summary_text: Full formatted summary text
        issue: Primary issue identified from the conversation
        attempted_solutions: List of solutions that were attempted
        current_status: Current state (resolved/unresolved/awaiting_response)
        word_count: Total word count of the summary
        generation_time_ms: Time to generate the summary in milliseconds

    Example:
        >>> summary = ConversationSummary(
        ...     summary_text="Issue: Payment failed. Tried: Reset card. Status: Unresolved.",
        ...     issue="Payment failed",
        ...     attempted_solutions=["Reset card"],
        ...     current_status="unresolved",
        ...     word_count=10,
        ...     generation_time_ms=5.2
        ... )
        >>> summary.to_dict()
        {'summary_text': 'Issue: Payment failed...', ...}
    """

    summary_text: str = Field(description="Full formatted summary text")
    issue: str = Field(description="Primary issue identified")
    attempted_solutions: list[str] = Field(
        default_factory=list,
        description="List of solutions attempted",
    )
    current_status: str = Field(
        description="Current state: resolved/unresolved/awaiting_response"
    )
    word_count: int = Field(description="Total word count of summary")
    generation_time_ms: float = Field(description="Time to generate in milliseconds")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields serialized to JSON-compatible types

        Example:
            >>> summary.to_dict()
            {'summary_text': '...', 'issue': '...', ...}
        """
        return self.model_dump(mode="json")
