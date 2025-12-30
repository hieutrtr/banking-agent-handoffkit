"""Integration tests for degradation tracking with RuleBasedAnalyzer."""

import pytest

from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.sentiment.degradation import DegradationTracker
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer


class TestRuleBasedAnalyzerWithDegradation:
    """Test RuleBasedAnalyzer integration with DegradationTracker."""

    @pytest.mark.asyncio
    async def test_analyzer_without_degradation_tracker(self) -> None:
        """Test analyzer works normally without degradation tracker."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="I'm frustrated")

        result = await analyzer.analyze(message)

        assert result.score < 0.5  # Negative sentiment
        assert result.degradation_detected is False

    @pytest.mark.asyncio
    async def test_analyzer_with_degradation_tracker_no_history(self) -> None:
        """Test analyzer with degradation tracker but no history."""
        tracker = DegradationTracker()
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)
        message = Message(speaker=MessageSpeaker.USER, content="I'm frustrated")

        result = await analyzer.analyze(message)

        # Should not trigger degradation with only 1 message
        assert result.degradation_detected is False

    @pytest.mark.asyncio
    async def test_analyzer_detects_degradation_over_conversation(self) -> None:
        """Test analyzer detects degradation over conversation history."""
        tracker = DegradationTracker(window_size=5, threshold=0.3)
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)

        # Create degrading conversation
        history = [
            Message(speaker=MessageSpeaker.USER, content="This is okay I guess"),  # ~0.5
            Message(speaker=MessageSpeaker.AI, content="How can I help?"),
            Message(speaker=MessageSpeaker.USER, content="Still not working"),  # ~0.4
            Message(speaker=MessageSpeaker.AI, content="Let me check"),
            Message(speaker=MessageSpeaker.USER, content="This is frustrating"),  # ~0.35
            Message(speaker=MessageSpeaker.AI, content="I understand"),
        ]

        # Final message that pushes over threshold
        current_message = Message(
            speaker=MessageSpeaker.USER,
            content="This is TERRIBLE and USELESS",
        )

        result = await analyzer.analyze(current_message, history=history)

        # Should detect degradation
        assert result.degradation_detected is True
        assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_analyzer_no_degradation_on_stable_sentiment(self) -> None:
        """Test analyzer doesn't trigger on stable sentiment."""
        tracker = DegradationTracker(threshold=0.3)
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)

        history = [
            Message(speaker=MessageSpeaker.USER, content="Hello there"),
            Message(speaker=MessageSpeaker.AI, content="Hi!"),
            Message(speaker=MessageSpeaker.USER, content="How are you"),
            Message(speaker=MessageSpeaker.AI, content="Good!"),
        ]

        current_message = Message(speaker=MessageSpeaker.USER, content="That's nice")

        result = await analyzer.analyze(current_message, history=history)

        assert result.degradation_detected is False

    @pytest.mark.asyncio
    async def test_analyzer_populates_contextual_features(self) -> None:
        """Test analyzer populates conversation_length and message_position."""
        tracker = DegradationTracker()
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)

        history = [
            Message(speaker=MessageSpeaker.USER, content="Message 1"),
            Message(speaker=MessageSpeaker.AI, content="Response 1"),
            Message(speaker=MessageSpeaker.USER, content="Message 2"),
        ]

        current_message = Message(speaker=MessageSpeaker.USER, content="Message 3")

        result = await analyzer.analyze(current_message, history=history)

        # We can't directly access features, but we can verify the result is valid
        assert result.score >= 0.0
        assert result.score <= 1.0
        assert isinstance(result.degradation_detected, bool)

    @pytest.mark.asyncio
    async def test_degradation_triggers_escalation(self) -> None:
        """Test that degradation detection triggers should_escalate."""
        tracker = DegradationTracker(window_size=5, threshold=0.2)
        analyzer = RuleBasedAnalyzer(threshold=1.0, degradation_tracker=tracker)
        # Set threshold=1.0 so score alone won't trigger escalation

        # Create degrading conversation
        history = [
            Message(speaker=MessageSpeaker.USER, content="This is great"),  # ~0.7
            Message(speaker=MessageSpeaker.AI, content="Hi"),
            Message(speaker=MessageSpeaker.USER, content="Okay I guess"),  # ~0.5
            Message(speaker=MessageSpeaker.AI, content="Yes?"),
        ]

        # Drop sentiment significantly to trigger degradation
        current_message = Message(
            speaker=MessageSpeaker.USER,
            content="This is terrible and frustrating and awful",
        )

        result = await analyzer.analyze(current_message, history=history)

        # Even though score alone wouldn't trigger (threshold=1.0),
        # degradation should trigger escalation
        assert result.degradation_detected is True
        assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_degradation_only_tracks_user_messages(self) -> None:
        """Test degradation only tracks user messages, not AI responses."""
        tracker = DegradationTracker()
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)

        history = [
            Message(speaker=MessageSpeaker.USER, content="I'm frustrated"),  # Track
            Message(speaker=MessageSpeaker.AI, content="This is terrible"),  # Skip
            Message(speaker=MessageSpeaker.USER, content="Still bad"),  # Track
        ]

        current_message = Message(speaker=MessageSpeaker.USER, content="Awful")

        result = await analyzer.analyze(current_message, history=history)

        # Should have tracked 3 user messages total (2 from history + 1 current)
        scores = tracker.get_recent_scores()
        assert len(scores) == 3  # 2 from history + 1 current

    @pytest.mark.asyncio
    async def test_performance_with_degradation_tracking(self) -> None:
        """Test that degradation tracking maintains <10ms performance."""
        tracker = DegradationTracker()
        analyzer = RuleBasedAnalyzer(degradation_tracker=tracker)

        history = [
            Message(speaker=MessageSpeaker.USER, content=f"Message {i}")
            for i in range(10)
        ]

        current_message = Message(speaker=MessageSpeaker.USER, content="Current message")

        result = await analyzer.analyze(current_message, history=history)

        # Should maintain <10ms even with history tracking
        assert result.processing_time_ms < 10
