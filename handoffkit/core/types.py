"""HandoffKit Core Type Definitions.

This module provides the core data models for HandoffKit, including:
- Message: Represents a single message in a conversation
- MessageSpeaker: Enum for message speaker types (user/ai)
- ConversationContext: Complete context for handoff
- Various result types for triggers, sentiment, and handoff operations

Example usage:
    >>> from handoffkit import Message, MessageSpeaker
    >>> msg = Message(speaker=MessageSpeaker.USER, content="Hello")
    >>> msg = Message(speaker="user", content="Hello")  # String also works
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now() -> datetime:
    """Return current UTC time in a timezone-aware format."""
    return datetime.now(timezone.utc)


class MessageSpeaker(str, Enum):
    """Speaker types for messages in a conversation.

    Attributes:
        USER: Message from the human user
        AI: Message from the AI assistant
        SYSTEM: System-level message (instructions, context)

    Example:
        >>> speaker = MessageSpeaker.USER
        >>> speaker.value
        'user'
    """

    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class HandoffPriority(str, Enum):
    """Priority levels for handoff requests."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class HandoffStatus(str, Enum):
    """Status of a handoff request."""

    PENDING = "pending"
    ROUTED = "routed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class TriggerType(str, Enum):
    """Types of handoff triggers."""

    DIRECT_REQUEST = "direct_request"
    FAILURE_PATTERN = "failure_pattern"
    CRITICAL_KEYWORD = "critical_keyword"
    SENTIMENT_ESCALATION = "sentiment_escalation"
    SENTIMENT_DEGRADATION = "sentiment_degradation"
    CUSTOM_RULE = "custom_rule"


# Mapping for backward compatibility with string inputs
_SPEAKER_ALIASES: dict[str, MessageSpeaker] = {
    "user": MessageSpeaker.USER,
    "ai": MessageSpeaker.AI,
    "assistant": MessageSpeaker.AI,  # Common alias
    "system": MessageSpeaker.SYSTEM,
}


class Message(BaseModel):
    """A single message in a conversation.

    Attributes:
        speaker: Who sent the message (user, ai, or system)
        content: The message text content
        timestamp: When the message was created (defaults to now)
        metadata: Optional additional data about the message

    Example:
        >>> msg = Message(speaker=MessageSpeaker.USER, content="Hello!")
        >>> msg = Message(speaker="user", content="Hello!")  # String input works too
        >>> msg.speaker
        <MessageSpeaker.USER: 'user'>

    Raises:
        ValidationError: If speaker is not a valid MessageSpeaker value or alias
    """

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    speaker: MessageSpeaker = Field(
        description="Who sent the message: 'user', 'ai', or 'system'"
    )
    content: str = Field(description="The message text content")
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the message was created",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional data about the message",
    )

    @field_validator("speaker", mode="before")
    @classmethod
    def validate_speaker(cls, v: Union[str, MessageSpeaker]) -> MessageSpeaker:
        """Validate and coerce speaker to MessageSpeaker enum.

        Accepts both MessageSpeaker enum values and string aliases
        ('user', 'ai', 'assistant', 'system').

        Args:
            v: The speaker value to validate

        Returns:
            MessageSpeaker: The validated enum value

        Raises:
            ValueError: If the value is not a valid speaker type
        """
        if isinstance(v, MessageSpeaker):
            return v

        if isinstance(v, str):
            lower_v = v.lower().strip()
            if lower_v in _SPEAKER_ALIASES:
                return _SPEAKER_ALIASES[lower_v]

            valid_values = list(_SPEAKER_ALIASES.keys())
            raise ValueError(
                f"Invalid speaker value '{v}'. "
                f"Valid options are: {', '.join(valid_values)}. "
                f"Example: Message(speaker='user', content='Hello')"
            )

        raise ValueError(
            f"Speaker must be a string or MessageSpeaker enum, got {type(v).__name__}. "
            f"Valid options are: 'user', 'ai', 'assistant', 'system'. "
            f"Example: Message(speaker=MessageSpeaker.USER, content='Hello')"
        )


class ConversationContext(BaseModel):
    """Complete context for a conversation requiring handoff."""

    conversation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: Optional[str] = None
    messages: list[Message] = Field(default_factory=list)
    entities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)


class TriggerResult(BaseModel):
    """Result from a trigger evaluation."""

    triggered: bool
    trigger_type: Optional[TriggerType] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SentimentResult(BaseModel):
    """Result from sentiment analysis."""

    score: float = Field(ge=-1.0, le=1.0)
    frustration_level: float = Field(default=0.0, ge=0.0, le=1.0)
    should_escalate: bool = False
    tier_used: str = "rule_based"
    processing_time_ms: float = 0.0
    degradation_detected: bool = False


class HandoffDecision(BaseModel):
    """Decision on whether to perform a handoff."""

    should_handoff: bool
    priority: HandoffPriority = HandoffPriority.MEDIUM
    trigger_results: list[TriggerResult] = Field(default_factory=list)
    sentiment_result: Optional[SentimentResult] = None
    reason: Optional[str] = None
    suggested_department: Optional[str] = None


class HandoffResult(BaseModel):
    """Result of executing a handoff."""

    success: bool
    handoff_id: Optional[str] = None
    status: HandoffStatus = HandoffStatus.PENDING
    assigned_agent: Optional[str] = None
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
