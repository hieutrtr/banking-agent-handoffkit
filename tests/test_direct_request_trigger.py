"""Tests for DirectRequestTrigger.

This module tests the direct request detection trigger which identifies
when users explicitly request human assistance.
"""

import time

import pytest

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.direct_request import DirectRequestTrigger


class TestDirectRequestTriggerBasic:
    """Basic tests for DirectRequestTrigger evaluate method."""

    @pytest.fixture
    def trigger(self) -> DirectRequestTrigger:
        """Create a DirectRequestTrigger instance."""
        return DirectRequestTrigger()

    @pytest.mark.asyncio
    async def test_detect_talk_to_human(self, trigger: DirectRequestTrigger):
        """Test detection of 'I want to talk to a human'."""
        message = Message(speaker="user", content="I want to talk to a human")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.confidence > 0.8
        assert result.trigger_type == TriggerType.DIRECT_REQUEST

    @pytest.mark.asyncio
    async def test_normal_question_not_triggered(self, trigger: DirectRequestTrigger):
        """Test that normal questions don't trigger."""
        message = Message(speaker="user", content="What is my account balance?")
        result = await trigger.evaluate(message)

        assert result.triggered is False
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_returns_trigger_result(self, trigger: DirectRequestTrigger):
        """Test that evaluate returns a TriggerResult."""
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message)

        assert isinstance(result, TriggerResult)


class TestDirectRequestPatternVariations:
    """Tests for various phrasings of direct requests (AC #3)."""

    @pytest.fixture
    def trigger(self) -> DirectRequestTrigger:
        """Create a DirectRequestTrigger instance."""
        return DirectRequestTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("phrase", [
        # Basic agent/representative requests
        "I want to talk to an agent",
        "Let me speak with a representative",
        "Connect me to a person",
        "I need to speak to someone",
        # Operator/support variations (Task 2.1)
        "Get me an operator",
        "Transfer me to support",
        "I want to speak to customer support",
        # Escalation requests (Task 2.2)
        "I need to escalate this",
        "Let me talk to a supervisor",
        "I want to speak to a manager",
        "Please escalate this issue",
        # Frustrated requests (Task 2.3)
        "Just get me a human",
        "Please transfer me now",
        "I demand to speak with someone",
        # Real person variations
        "I need a real person",
        "I want a live agent",
        "Get me a human agent",
    ])
    async def test_detects_common_variations(self, trigger: DirectRequestTrigger, phrase: str):
        """Test detection of common request variations."""
        message = Message(speaker="user", content=phrase)
        result = await trigger.evaluate(message)

        assert result.triggered is True, f"Failed to detect: '{phrase}'"
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_case_insensitivity(self, trigger: DirectRequestTrigger):
        """Test that patterns are case insensitive."""
        variations = [
            "I WANT TO TALK TO A HUMAN",
            "i want to talk to a human",
            "I Want To Talk To A Human",
        ]
        for phrase in variations:
            message = Message(speaker="user", content=phrase)
            result = await trigger.evaluate(message)
            assert result.triggered is True, f"Case sensitivity failed for: '{phrase}'"


class TestDirectRequestNegativePatterns:
    """Tests for avoiding false positives (Task 2.4)."""

    @pytest.fixture
    def trigger(self) -> DirectRequestTrigger:
        """Create a DirectRequestTrigger instance."""
        return DirectRequestTrigger()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("phrase", [
        # Should NOT trigger
        "How do I reset my password?",
        "What's my account balance?",
        "I'm having trouble logging in",
        "Can you help me with billing?",
        "Thanks for the help!",
        "That solved my problem",
        # Negative statements that mention humans but don't request them
        "I don't need to talk to a human",
        "I'm not asking for an agent",
        "No need for a representative",
    ])
    async def test_no_false_positives(self, trigger: DirectRequestTrigger, phrase: str):
        """Test that normal questions don't trigger false positives."""
        message = Message(speaker="user", content=phrase)
        result = await trigger.evaluate(message)

        assert result.triggered is False, f"False positive for: '{phrase}'"


class TestDirectRequestPerformance:
    """Tests for performance requirements (AC #4)."""

    @pytest.fixture
    def trigger(self) -> DirectRequestTrigger:
        """Create a DirectRequestTrigger instance."""
        return DirectRequestTrigger()

    @pytest.mark.asyncio
    async def test_evaluation_under_100ms(self, trigger: DirectRequestTrigger):
        """Test that evaluation completes in <100ms (AC #4)."""
        message = Message(speaker="user", content="I want to talk to a human please")

        start_time = time.perf_counter()
        result = await trigger.evaluate(message)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 100, f"Evaluation took {elapsed_ms:.2f}ms, expected <100ms"
        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_duration_in_metadata(self, trigger: DirectRequestTrigger):
        """Test that duration_ms is included in result metadata."""
        message = Message(speaker="user", content="Hello there")
        result = await trigger.evaluate(message)

        assert "duration_ms" in result.metadata
        assert isinstance(result.metadata["duration_ms"], float)
        assert result.metadata["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_multiple_evaluations_fast(self, trigger: DirectRequestTrigger):
        """Test that 100 evaluations complete in <1 second."""
        messages = [
            Message(speaker="user", content=f"Test message {i}")
            for i in range(100)
        ]

        start_time = time.perf_counter()
        for message in messages:
            await trigger.evaluate(message)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 100 evaluations should complete in <1000ms (10ms each on average)
        assert elapsed_ms < 1000, f"100 evaluations took {elapsed_ms:.2f}ms"


class TestDirectRequestTriggerProperties:
    """Tests for trigger properties and initialization."""

    def test_trigger_name(self):
        """Test that trigger_name property returns correct value."""
        trigger = DirectRequestTrigger()
        assert trigger.trigger_name == "direct_request"

    def test_custom_patterns(self):
        """Test that custom patterns can be provided."""
        custom_patterns = [r"(?i)\bcustom\s+pattern"]
        trigger = DirectRequestTrigger(patterns=custom_patterns)

        # Verify custom patterns are used
        assert len(trigger._compiled_patterns) == 1

    @pytest.mark.asyncio
    async def test_custom_pattern_matches(self):
        """Test that custom patterns work correctly."""
        custom_patterns = [r"(?i)\bhelp\s+me\s+out"]
        trigger = DirectRequestTrigger(patterns=custom_patterns)

        message = Message(speaker="user", content="Please help me out with this")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_reason_includes_matched_pattern(self):
        """Test that reason field includes the matched pattern."""
        trigger = DirectRequestTrigger()
        message = Message(speaker="user", content="I want to talk to a human")
        result = await trigger.evaluate(message)

        assert result.triggered is True
        assert result.reason is not None
        assert "talk to a human" in result.reason.lower()
