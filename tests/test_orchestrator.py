"""Tests for HandoffOrchestrator base interface."""

import pytest
from pydantic import ValidationError

from handoffkit import (
    HandoffConfig,
    HandoffOrchestrator,
    HandoffResult,
    Message,
    MessageSpeaker,
    TriggerConfig,
    TriggerResult,
)


class TestHandoffOrchestratorConstructor:
    """Test HandoffOrchestrator constructor and initialization."""

    def test_constructor_with_helpdesk_only(self):
        """Test creating orchestrator with only helpdesk parameter."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert orchestrator.helpdesk == "zendesk"
        assert orchestrator.config is not None
        assert isinstance(orchestrator.config, HandoffConfig)

    def test_constructor_with_default_helpdesk(self):
        """Test orchestrator uses zendesk as default helpdesk."""
        orchestrator = HandoffOrchestrator()
        assert orchestrator.helpdesk == "zendesk"

    def test_constructor_with_intercom(self):
        """Test creating orchestrator with intercom helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="intercom")
        assert orchestrator.helpdesk == "intercom"

    def test_constructor_with_custom_helpdesk(self):
        """Test creating orchestrator with custom helpdesk."""
        orchestrator = HandoffOrchestrator(helpdesk="custom")
        assert orchestrator.helpdesk == "custom"

    def test_constructor_with_helpdesk_and_config(self):
        """Test creating orchestrator with both helpdesk and config."""
        config = HandoffConfig(max_context_messages=50)
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)
        assert orchestrator.helpdesk == "zendesk"
        assert orchestrator.config is config
        assert orchestrator.config.max_context_messages == 50

    def test_constructor_invalid_helpdesk_raises_error(self):
        """Test invalid helpdesk value raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            HandoffOrchestrator(helpdesk="invalid_provider")

        error_message = str(exc_info.value)
        assert "helpdesk" in error_message.lower() or "invalid" in error_message.lower()

    def test_constructor_creates_default_config(self):
        """Test orchestrator creates default config when none provided."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert orchestrator.config.triggers.failure_threshold == 3
        assert orchestrator.config.triggers.sentiment_threshold == 0.3

    def test_constructor_custom_config_overrides_defaults(self):
        """Test custom config overrides default values."""
        custom_config = HandoffConfig(
            triggers=TriggerConfig(failure_threshold=2, sentiment_threshold=0.5)
        )
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=custom_config)
        assert orchestrator.config.triggers.failure_threshold == 2
        assert orchestrator.config.triggers.sentiment_threshold == 0.5


class TestHandoffOrchestratorProperties:
    """Test property accessors for HandoffOrchestrator."""

    def test_helpdesk_property(self):
        """Test helpdesk property returns correct value."""
        orchestrator = HandoffOrchestrator(helpdesk="intercom")
        assert orchestrator.helpdesk == "intercom"

    def test_config_property(self):
        """Test config property returns HandoffConfig."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        config = orchestrator.config
        assert isinstance(config, HandoffConfig)

    def test_triggers_property_shortcut(self):
        """Test triggers property is shortcut to config.triggers."""
        custom_config = HandoffConfig(
            triggers=TriggerConfig(failure_threshold=4)
        )
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=custom_config)
        assert orchestrator.triggers is orchestrator.config.triggers
        assert orchestrator.triggers.failure_threshold == 4


class TestShouldHandoffMethod:
    """Test should_handoff() method functionality."""

    def test_should_handoff_returns_tuple(self):
        """Test should_handoff returns a tuple."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="Hello")]
        result = orchestrator.should_handoff(messages, "Hello")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_should_handoff_returns_false_none_by_default(self):
        """Test should_handoff returns (False, None) by default."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="Hello")]
        should_handoff, trigger_result = orchestrator.should_handoff(messages, "Hello")
        assert should_handoff is False
        assert trigger_result is None

    def test_should_handoff_with_empty_conversation(self):
        """Test should_handoff with empty conversation list."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        should_handoff, trigger_result = orchestrator.should_handoff([], "New message")
        assert should_handoff is False
        assert trigger_result is None

    def test_should_handoff_with_populated_conversation(self):
        """Test should_handoff with populated conversation."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [
            Message(speaker="user", content="I need help with my order"),
            Message(speaker="ai", content="I'd be happy to help!"),
            Message(speaker="user", content="I want to talk to a human"),
        ]
        should_handoff, trigger_result = orchestrator.should_handoff(
            messages, "I want to talk to a human"
        )
        # Default stub returns (False, None) - actual detection comes in Epic 2
        assert should_handoff is False
        assert trigger_result is None

    def test_should_handoff_no_exceptions(self):
        """Test should_handoff does not raise exceptions with valid input."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="Test")]
        # Should not raise any exception
        result = orchestrator.should_handoff(messages, "Test message")
        assert result == (False, None)

    def test_should_handoff_accepts_message_list(self):
        """Test should_handoff accepts list of Message objects."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [
            Message(speaker=MessageSpeaker.USER, content="Hello"),
            Message(speaker=MessageSpeaker.AI, content="Hi there!"),
        ]
        # Should accept Message objects without error
        should_handoff, trigger_result = orchestrator.should_handoff(messages, "Hello")
        assert isinstance(should_handoff, bool)


class TestCreateHandoffMethod:
    """Test create_handoff() method functionality."""

    def test_create_handoff_returns_handoff_result(self):
        """Test create_handoff returns a HandoffResult."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="I need help")]
        result = orchestrator.create_handoff(messages)
        assert isinstance(result, HandoffResult)

    def test_create_handoff_with_metadata(self):
        """Test create_handoff accepts metadata parameter."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="I need help")]
        metadata = {"user_id": "123", "channel": "web"}
        result = orchestrator.create_handoff(messages, metadata=metadata)
        assert isinstance(result, HandoffResult)

    def test_create_handoff_without_metadata(self):
        """Test create_handoff works without metadata."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="Help please")]
        result = orchestrator.create_handoff(messages)
        assert isinstance(result, HandoffResult)

    def test_create_handoff_returns_pending_status(self):
        """Test create_handoff returns pending result (stub implementation)."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        messages = [Message(speaker="user", content="I need help")]
        result = orchestrator.create_handoff(messages)
        # Stub implementation returns pending status
        assert result.success is False or result.status.value == "pending"

    def test_create_handoff_with_empty_conversation(self):
        """Test create_handoff with empty conversation."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        result = orchestrator.create_handoff([])
        assert isinstance(result, HandoffResult)


class TestOrchestratorMethodExistence:
    """Test that required methods exist on HandoffOrchestrator."""

    def test_has_should_handoff_method(self):
        """Test orchestrator has should_handoff method."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert hasattr(orchestrator, "should_handoff")
        assert callable(orchestrator.should_handoff)

    def test_has_create_handoff_method(self):
        """Test orchestrator has create_handoff method."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert hasattr(orchestrator, "create_handoff")
        assert callable(orchestrator.create_handoff)

    def test_has_config_property(self):
        """Test orchestrator has config property."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert hasattr(orchestrator, "config")

    def test_has_helpdesk_property(self):
        """Test orchestrator has helpdesk property."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert hasattr(orchestrator, "helpdesk")

    def test_has_triggers_property(self):
        """Test orchestrator has triggers property."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")
        assert hasattr(orchestrator, "triggers")
