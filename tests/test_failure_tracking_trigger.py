"""Tests for FailureTrackingTrigger.

This module tests the failure pattern tracking trigger which identifies
when the AI has failed to help users multiple times.
"""

import time

import pytest

from handoffkit.core.types import Message, MessageSpeaker, TriggerResult, TriggerType
from handoffkit.triggers.failure_tracking import FailureTrackingTrigger


class TestFailureTrackingTriggerBasic:
    """Basic tests for FailureTrackingTrigger evaluate method."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a FailureTrackingTrigger instance with default threshold."""
        return FailureTrackingTrigger()

    @pytest.mark.asyncio
    async def test_returns_trigger_result(self, trigger: FailureTrackingTrigger):
        """Test that evaluate returns a TriggerResult."""
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message, history=[])

        assert isinstance(result, TriggerResult)

    @pytest.mark.asyncio
    async def test_no_history_does_not_trigger(self, trigger: FailureTrackingTrigger):
        """Test that no history means no trigger."""
        message = Message(speaker="user", content="What is my balance?")
        result = await trigger.evaluate(message, history=None)

        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_empty_history_does_not_trigger(self, trigger: FailureTrackingTrigger):
        """Test that empty history means no trigger."""
        message = Message(speaker="user", content="What is my balance?")
        result = await trigger.evaluate(message, history=[])

        assert result.triggered is False


class TestRepeatedQuestions:
    """Tests for repeated question detection (AC #1)."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a FailureTrackingTrigger instance."""
        return FailureTrackingTrigger(failure_threshold=3)

    @pytest.mark.asyncio
    async def test_repeated_question_3_times_triggers(self, trigger: FailureTrackingTrigger):
        """Test that repeating the same question 3 times with AI failures triggers (AC #1)."""
        history = [
            Message(speaker="user", content="What is my account balance?"),
            Message(speaker="ai", content="I'm not sure about that."),
            Message(speaker="user", content="What is my account balance?"),
            Message(speaker="ai", content="I don't understand your question."),
            Message(speaker="user", content="What is my account balance?"),
            Message(speaker="ai", content="I cannot help with that."),
        ]
        current = Message(speaker="user", content="What is my account balance?")

        result = await trigger.evaluate(current, history=history)

        assert result.triggered is True
        assert result.trigger_type == TriggerType.FAILURE_PATTERN
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_similar_questions_trigger(self, trigger: FailureTrackingTrigger):
        """Test that similar (not exact) questions with AI failures also trigger."""
        history = [
            Message(speaker="user", content="What is my balance?"),
            Message(speaker="ai", content="I'm not sure."),
            Message(speaker="user", content="Can you tell me my balance?"),
            Message(speaker="ai", content="I don't understand."),
            Message(speaker="user", content="Show me my balance please"),
            Message(speaker="ai", content="I cannot help with that."),
        ]
        current = Message(speaker="user", content="My balance please")

        result = await trigger.evaluate(current, history=history)

        assert result.triggered is True

    @pytest.mark.asyncio
    async def test_different_questions_do_not_trigger(self, trigger: FailureTrackingTrigger):
        """Test that different questions don't trigger repeated question detection."""
        history = [
            Message(speaker="user", content="What is my balance?"),
            Message(speaker="ai", content="Your balance is $100."),
            Message(speaker="user", content="When is my next payment due?"),
            Message(speaker="ai", content="Your next payment is due on the 15th."),
        ]
        current = Message(speaker="user", content="How do I change my password?")

        result = await trigger.evaluate(current, history=history)

        assert result.triggered is False


class TestAIFailurePatterns:
    """Tests for AI failure phrase detection (AC #2)."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a trigger with threshold=2."""
        return FailureTrackingTrigger(failure_threshold=2)

    @pytest.mark.asyncio
    async def test_ai_dont_understand_triggers_on_threshold(self, trigger: FailureTrackingTrigger):
        """Test that AI 'I don't understand' triggers on 2nd failure (AC #2)."""
        history = [
            Message(speaker="user", content="What's my balance?"),
            Message(speaker="ai", content="I don't understand your question."),
            Message(speaker="user", content="My account balance please"),
            Message(speaker="ai", content="I'm not sure what you mean."),
        ]
        current = Message(speaker="user", content="Balance!")

        result = await trigger.evaluate(current, history=history)

        # 2 AI failures, threshold is 2, should trigger
        assert result.triggered is True
        assert result.trigger_type == TriggerType.FAILURE_PATTERN

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure_phrase", [
        "I don't understand",
        "I'm not sure what you mean",
        "I cannot help with that",
        "Could you please rephrase",
        "I'm having trouble understanding",
    ])
    async def test_various_ai_failure_phrases(self, failure_phrase: str):
        """Test various AI failure phrases are detected."""
        trigger = FailureTrackingTrigger(failure_threshold=2)
        history = [
            Message(speaker="user", content="Help me"),
            Message(speaker="ai", content=failure_phrase),
            Message(speaker="user", content="I need help"),
            Message(speaker="ai", content="I don't know how to help."),
        ]
        current = Message(speaker="user", content="Please help")

        result = await trigger.evaluate(current, history=history)

        assert result.triggered is True, f"Failed to detect: '{failure_phrase}'"


class TestUserFrustrationPatterns:
    """Tests for user frustration detection."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a trigger with threshold=2."""
        return FailureTrackingTrigger(failure_threshold=2)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("frustration_phrase", [
        "You're not helping",
        "That's not what I asked",
        "I already told you",
        "You keep saying the same thing",
        "This doesn't work",
    ])
    async def test_user_frustration_phrases(self, trigger: FailureTrackingTrigger, frustration_phrase: str):
        """Test that user frustration phrases contribute to failure count."""
        history = [
            Message(speaker="user", content="What is my balance?"),
            Message(speaker="ai", content="I can help with accounts."),
            Message(speaker="user", content=frustration_phrase),
            Message(speaker="ai", content="I'm not sure what you need."),
        ]
        current = Message(speaker="user", content="I need my balance!")

        result = await trigger.evaluate(current, history=history)

        # User frustration + AI failure should trigger at threshold=2
        assert result.triggered is True, f"Failed to detect frustration: '{frustration_phrase}'"


class TestSuccessReset:
    """Tests for success indicator reset logic (AC #3)."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a trigger with threshold=3."""
        return FailureTrackingTrigger(failure_threshold=3)

    @pytest.mark.asyncio
    async def test_success_resets_failure_counter(self, trigger: FailureTrackingTrigger):
        """Test that success resets the failure counter (AC #3)."""
        history = [
            Message(speaker="user", content="What is my balance?"),
            Message(speaker="ai", content="I don't understand."),
            Message(speaker="user", content="My account balance"),
            Message(speaker="ai", content="Your balance is $500."),
            Message(speaker="user", content="Thanks, that helps!"),  # Success indicator
            Message(speaker="ai", content="You're welcome!"),
            Message(speaker="user", content="What are the fees?"),
            Message(speaker="ai", content="I'm not sure about fees."),
        ]
        current = Message(speaker="user", content="Tell me about fees")

        result = await trigger.evaluate(current, history=history)

        # Only 1 failure after success, should NOT trigger (threshold is 3)
        assert result.triggered is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("success_phrase", [
        "Thanks",
        "Thank you",
        "That helps",
        "That worked",
        "Perfect",
        "Great",
        "Got it",
        "Understood",
        "Awesome",
        "Exactly",
    ])
    async def test_various_success_phrases_reset(self, trigger: FailureTrackingTrigger, success_phrase: str):
        """Test that various success phrases reset the counter."""
        history = [
            Message(speaker="user", content="Help me"),
            Message(speaker="ai", content="I don't understand."),
            Message(speaker="user", content="Explain this"),
            Message(speaker="ai", content="Here's the explanation..."),
            Message(speaker="user", content=success_phrase),
            Message(speaker="ai", content="Happy to help!"),
            Message(speaker="user", content="Another question"),
            Message(speaker="ai", content="I'm not sure."),
        ]
        current = Message(speaker="user", content="Please help")

        result = await trigger.evaluate(current, history=history)

        # Should not trigger because success reset the counter
        assert result.triggered is False, f"Success phrase '{success_phrase}' didn't reset counter"


class TestConfigurableThreshold:
    """Tests for configurable threshold (AC #5)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("threshold", [1, 2, 3, 4, 5])
    async def test_respects_configured_threshold(self, threshold: int):
        """Test that trigger respects configured threshold (AC #5)."""
        trigger = FailureTrackingTrigger(failure_threshold=threshold)

        # Build history with exactly threshold failures
        history = []
        for i in range(threshold):
            history.append(Message(speaker="user", content=f"Question {i}"))
            history.append(Message(speaker="ai", content="I don't understand."))

        current = Message(speaker="user", content="Same question again")

        result = await trigger.evaluate(current, history=history)

        # At exactly threshold failures, should trigger
        assert result.triggered is True, f"Failed with threshold={threshold}"

    @pytest.mark.asyncio
    async def test_below_threshold_does_not_trigger(self):
        """Test that below threshold does not trigger."""
        trigger = FailureTrackingTrigger(failure_threshold=3)

        history = [
            Message(speaker="user", content="Question 1"),
            Message(speaker="ai", content="I don't understand."),
        ]
        current = Message(speaker="user", content="Question 2")

        result = await trigger.evaluate(current, history=history)

        # Only 1 failure, threshold is 3
        assert result.triggered is False


class TestBotLoopDetection:
    """Tests for bot loop detection (same AI response repeated)."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a trigger with threshold=2."""
        return FailureTrackingTrigger(failure_threshold=2)

    @pytest.mark.asyncio
    async def test_bot_loop_detected(self, trigger: FailureTrackingTrigger):
        """Test that repeated identical AI responses trigger."""
        history = [
            Message(speaker="user", content="Help me"),
            Message(speaker="ai", content="I can help with general questions about your account."),
            Message(speaker="user", content="I need specific help"),
            Message(speaker="ai", content="I can help with general questions about your account."),  # Same response
        ]
        current = Message(speaker="user", content="You're not helping me")

        result = await trigger.evaluate(current, history=history)

        # Bot loop + user frustration = 2 >= threshold
        assert result.triggered is True


class TestPerformance:
    """Tests for performance requirements (AC #4)."""

    @pytest.fixture
    def trigger(self) -> FailureTrackingTrigger:
        """Create a trigger instance."""
        return FailureTrackingTrigger()

    @pytest.mark.asyncio
    async def test_evaluation_under_100ms(self, trigger: FailureTrackingTrigger):
        """Test that evaluation completes in <100ms (AC #4)."""
        history = [
            Message(speaker="user", content=f"Question {i}")
            for i in range(10)
        ]
        current = Message(speaker="user", content="Final question")

        start_time = time.perf_counter()
        result = await trigger.evaluate(current, history=history)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 100, f"Evaluation took {elapsed_ms:.2f}ms, expected <100ms"

    @pytest.mark.asyncio
    async def test_duration_in_metadata(self, trigger: FailureTrackingTrigger):
        """Test that duration_ms is included in result metadata."""
        message = Message(speaker="user", content="Hello")
        result = await trigger.evaluate(message, history=[])

        assert "duration_ms" in result.metadata
        assert isinstance(result.metadata["duration_ms"], float)
        assert result.metadata["duration_ms"] >= 0


class TestTriggerProperties:
    """Tests for trigger properties."""

    def test_trigger_name(self):
        """Test that trigger_name property returns correct value."""
        trigger = FailureTrackingTrigger()
        assert trigger.trigger_name == "failure_tracking"

    def test_default_threshold(self):
        """Test default threshold is 3."""
        trigger = FailureTrackingTrigger()
        assert trigger._threshold == 3

    def test_custom_threshold(self):
        """Test custom threshold is respected."""
        trigger = FailureTrackingTrigger(failure_threshold=5)
        assert trigger._threshold == 5

    def test_failure_window(self):
        """Test failure_window parameter."""
        trigger = FailureTrackingTrigger(failure_window=10)
        assert trigger._window == 10
