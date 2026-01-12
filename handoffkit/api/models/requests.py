"""Request models for HandoffKit REST API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    content: str = Field(..., min_length=1, description="Message content")
    speaker: str = Field(..., description="Speaker type: 'user', 'ai', or 'system'")
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )


class CheckHandoffRequest(BaseModel):
    """Request body for checking if handoff should occur."""

    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique conversation identifier"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User identifier"
    )
    messages: List[ConversationMessage] = Field(
        ...,
        min_length=1,
        description="List of conversation messages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional conversation metadata"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context overrides"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [
                    {"content": "I need help", "speaker": "user"},
                    {"content": "How can I assist?", "speaker": "ai"}
                ],
                "metadata": {"channel": "web"},
                "context": {"priority": "high"}
            }
        }
    }


class CreateHandoffRequest(BaseModel):
    """Request body for creating a handoff."""

    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique conversation identifier"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User identifier"
    )
    messages: List[ConversationMessage] = Field(
        ...,
        min_length=1,
        description="List of conversation messages"
    )
    priority: Optional[str] = Field(
        default="MEDIUM",
        description="Handoff priority: LOW, MEDIUM, HIGH, URGENT, CRITICAL",
        json_schema_extra={"enum": ["LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"]}
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional conversation metadata"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context overrides"
    )
    skip_triggers: bool = Field(
        default=False,
        description="Skip trigger evaluation and create handoff directly"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv-123",
                "user_id": "user-456",
                "messages": [
                    {"content": "I need help with billing", "speaker": "user"},
                    {"content": "Let me transfer you to billing", "speaker": "ai"}
                ],
                "priority": "HIGH",
                "metadata": {"channel": "web", "product": "premium"},
                "skip_triggers": False
            }
        }
    }


class HandoffActionRequest(BaseModel):
    """Request body for handoff actions (cancel, reassign, etc.)."""

    handoff_id: str = Field(
        ...,
        min_length=1,
        description="Handoff identifier"
    )
    action: str = Field(
        ...,
        description="Action type: 'cancel', 'reassign', 'escalate'"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the action"
    )
    target: Optional[str] = Field(
        default=None,
        description="Target for reassign (agent_id or queue_name)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional action metadata"
    )