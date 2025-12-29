"""Tests for HandoffKit core type definitions."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from handoffkit import Message
from handoffkit.core.types import (
    MessageSpeaker,
    HandoffPriority,
    HandoffStatus,
    TriggerType,
    ConversationContext,
    TriggerResult,
    SentimentResult,
    HandoffDecision,
    HandoffResult,
)


class TestMessageSpeakerEnum:
    """Test MessageSpeaker enum functionality."""

    def test_enum_values(self):
        """Test enum has correct string values."""
        assert MessageSpeaker.USER.value == "user"
        assert MessageSpeaker.AI.value == "ai"
        assert MessageSpeaker.SYSTEM.value == "system"

    def test_enum_is_string_type(self):
        """Test enum values are strings."""
        assert isinstance(MessageSpeaker.USER, str)
        assert MessageSpeaker.USER == "user"


class TestMessageModel:
    """Test Message Pydantic model validation."""

    def test_create_with_enum(self):
        """Test creating Message with MessageSpeaker enum."""
        msg = Message(speaker=MessageSpeaker.USER, content="Hello")
        assert msg.speaker == MessageSpeaker.USER
        assert msg.content == "Hello"

    def test_create_with_string_user(self):
        """Test creating Message with 'user' string."""
        msg = Message(speaker="user", content="Hello")
        assert msg.speaker == MessageSpeaker.USER

    def test_create_with_string_ai(self):
        """Test creating Message with 'ai' string."""
        msg = Message(speaker="ai", content="Hello")
        assert msg.speaker == MessageSpeaker.AI

    def test_create_with_string_assistant_alias(self):
        """Test 'assistant' string is coerced to AI."""
        msg = Message(speaker="assistant", content="Hello")
        assert msg.speaker == MessageSpeaker.AI

    def test_create_with_string_system(self):
        """Test creating Message with 'system' string."""
        msg = Message(speaker="system", content="Instructions")
        assert msg.speaker == MessageSpeaker.SYSTEM

    def test_case_insensitive_speaker(self):
        """Test speaker string is case-insensitive."""
        msg1 = Message(speaker="USER", content="Hello")
        msg2 = Message(speaker="User", content="Hello")
        msg3 = Message(speaker="uSeR", content="Hello")
        assert msg1.speaker == MessageSpeaker.USER
        assert msg2.speaker == MessageSpeaker.USER
        assert msg3.speaker == MessageSpeaker.USER

    def test_speaker_with_whitespace(self):
        """Test speaker string strips whitespace."""
        msg = Message(speaker=" user ", content="Hello")
        assert msg.speaker == MessageSpeaker.USER

    def test_invalid_speaker_string(self):
        """Test invalid speaker raises ValidationError with helpful message."""
        with pytest.raises(ValidationError) as exc_info:
            Message(speaker="invalid", content="Hello")

        error_message = str(exc_info.value)
        assert "Invalid speaker value" in error_message
        assert "valid options" in error_message.lower()

    def test_invalid_speaker_type(self):
        """Test non-string speaker raises ValidationError with helpful message."""
        with pytest.raises(ValidationError) as exc_info:
            Message(speaker=123, content="Hello")

        error_message = str(exc_info.value)
        assert "int" in error_message.lower() or "string" in error_message.lower()

    def test_timestamp_auto_generated(self):
        """Test timestamp is auto-generated if not provided."""
        msg = Message(speaker="user", content="Hello")
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_timestamp_custom(self):
        """Test custom timestamp is accepted."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        msg = Message(speaker="user", content="Hello", timestamp=custom_time)
        assert msg.timestamp == custom_time

    def test_metadata_default_empty(self):
        """Test metadata defaults to empty dict."""
        msg = Message(speaker="user", content="Hello")
        assert msg.metadata == {}

    def test_metadata_custom(self):
        """Test custom metadata is accepted."""
        msg = Message(
            speaker="user",
            content="Hello",
            metadata={"intent": "greeting", "confidence": 0.95},
        )
        assert msg.metadata["intent"] == "greeting"
        assert msg.metadata["confidence"] == 0.95

    def test_empty_content_allowed(self):
        """Test empty content string is allowed."""
        msg = Message(speaker="user", content="")
        assert msg.content == ""

    def test_missing_required_fields(self):
        """Test missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Message(speaker="user")  # Missing content

        with pytest.raises(ValidationError):
            Message(content="Hello")  # Missing speaker


class TestConversationContext:
    """Test ConversationContext model."""

    def test_create_minimal(self):
        """Test creating with minimal required fields."""
        ctx = ConversationContext(conversation_id="conv-123")
        assert ctx.conversation_id == "conv-123"
        assert ctx.user_id is None
        assert ctx.messages == []

    def test_create_with_messages(self):
        """Test creating with messages list."""
        messages = [
            Message(speaker="user", content="Hello"),
            Message(speaker="ai", content="Hi there!"),
        ]
        ctx = ConversationContext(
            conversation_id="conv-123",
            messages=messages,
        )
        assert len(ctx.messages) == 2
        assert ctx.messages[0].speaker == MessageSpeaker.USER
        assert ctx.messages[1].speaker == MessageSpeaker.AI

    def test_optional_fields(self):
        """Test optional fields can be set."""
        ctx = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            session_id="session-789",
            channel="web",
            entities={"account_number": "****1234"},
            metadata={"source": "chatbot"},
        )
        assert ctx.user_id == "user-456"
        assert ctx.session_id == "session-789"
        assert ctx.channel == "web"


class TestTriggerResult:
    """Test TriggerResult model."""

    def test_create_triggered(self):
        """Test creating a triggered result."""
        result = TriggerResult(
            triggered=True,
            trigger_type=TriggerType.DIRECT_REQUEST,
            confidence=0.95,
            reason="User explicitly asked for human",
        )
        assert result.triggered is True
        assert result.trigger_type == TriggerType.DIRECT_REQUEST
        assert result.confidence == 0.95

    def test_create_not_triggered(self):
        """Test creating a not-triggered result."""
        result = TriggerResult(triggered=False)
        assert result.triggered is False
        assert result.trigger_type is None
        assert result.confidence == 1.0

    def test_confidence_range_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            TriggerResult(triggered=True, confidence=1.5)

        with pytest.raises(ValidationError):
            TriggerResult(triggered=True, confidence=-0.1)


class TestSentimentResult:
    """Test SentimentResult model."""

    def test_score_range(self):
        """Test score range validation (-1 to 1)."""
        result = SentimentResult(score=0.5)
        assert result.score == 0.5

        result = SentimentResult(score=-1.0)
        assert result.score == -1.0

        result = SentimentResult(score=1.0)
        assert result.score == 1.0

    def test_score_out_of_range(self):
        """Test score outside range raises error."""
        with pytest.raises(ValidationError):
            SentimentResult(score=1.5)

        with pytest.raises(ValidationError):
            SentimentResult(score=-1.5)

    def test_defaults(self):
        """Test default values."""
        result = SentimentResult(score=0.0)
        assert result.frustration_level == 0.0
        assert result.should_escalate is False
        assert result.tier_used == "rule_based"
        assert result.processing_time_ms == 0.0


class TestHandoffDecision:
    """Test HandoffDecision model."""

    def test_should_handoff_true(self):
        """Test decision to handoff."""
        decision = HandoffDecision(
            should_handoff=True,
            priority=HandoffPriority.HIGH,
            reason="Multiple triggers detected",
        )
        assert decision.should_handoff is True
        assert decision.priority == HandoffPriority.HIGH

    def test_should_handoff_false(self):
        """Test decision not to handoff."""
        decision = HandoffDecision(should_handoff=False)
        assert decision.should_handoff is False
        assert decision.priority == HandoffPriority.MEDIUM

    def test_with_trigger_results(self):
        """Test with trigger results list."""
        triggers = [
            TriggerResult(triggered=True, trigger_type=TriggerType.DIRECT_REQUEST),
            TriggerResult(triggered=True, trigger_type=TriggerType.SENTIMENT_ESCALATION),
        ]
        decision = HandoffDecision(
            should_handoff=True,
            trigger_results=triggers,
        )
        assert len(decision.trigger_results) == 2


class TestHandoffResult:
    """Test HandoffResult model."""

    def test_successful_handoff(self):
        """Test successful handoff result."""
        result = HandoffResult(
            success=True,
            handoff_id="hf-123",
            status=HandoffStatus.ASSIGNED,
            assigned_agent="agent-456",
            ticket_id="TKT-789",
            ticket_url="https://helpdesk.example.com/tickets/789",
        )
        assert result.success is True
        assert result.handoff_id == "hf-123"
        assert result.status == HandoffStatus.ASSIGNED

    def test_failed_handoff(self):
        """Test failed handoff result."""
        result = HandoffResult(
            success=False,
            error_message="Connection timeout to helpdesk API",
        )
        assert result.success is False
        assert result.error_message == "Connection timeout to helpdesk API"
        assert result.status == HandoffStatus.PENDING
