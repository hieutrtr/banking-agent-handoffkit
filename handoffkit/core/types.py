"""HandoffKit Core Type Definitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time in a timezone-aware format."""
    return datetime.now(timezone.utc)


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
    CUSTOM_RULE = "custom_rule"


class Message(BaseModel):
    """A single message in a conversation."""

    role: str = Field(pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


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
