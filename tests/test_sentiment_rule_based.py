"""Tests for rule-based sentiment analyzer (Tier 1)."""

import asyncio
import time
from typing import Optional

import pytest

from handoffkit.core.types import Message, MessageSpeaker, SentimentResult
from handoffkit.sentiment.models import SentimentFeatures
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer


class TestRuleBasedAnalyzerBasic:
    """Basic tests for RuleBasedAnalyzer initialization."""

    def test_analyzer_initializes(self) -> None:
        """Test analyzer can be instantiated."""
        analyzer = RuleBasedAnalyzer()
        assert analyzer is not None

    def test_analyzer_has_compiled_patterns(self) -> None:
        """Test analyzer pre-compiles regex patterns."""
        analyzer = RuleBasedAnalyzer()
        assert analyzer._negative_pattern is not None
        assert analyzer._positive_pattern is not None
        assert analyzer._frustration_pattern is not None

    def test_analyzer_accepts_threshold(self) -> None:
        """Test analyzer accepts custom threshold parameter."""
        analyzer = RuleBasedAnalyzer(threshold=0.4)
        assert analyzer._threshold == 0.4

    def test_analyzer_default_threshold(self) -> None:
        """Test analyzer uses default threshold of 0.3."""
        analyzer = RuleBasedAnalyzer()
        assert analyzer._threshold == 0.3


class TestKeywordScoring:
    """Tests for keyword-based sentiment scoring."""

    @pytest.mark.asyncio
    async def test_strong_negative_keywords_produce_low_score(self) -> None:
        """Test that strong negative keywords result in score < 0.3."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="This is terrible and awful!")
        result = await analyzer.analyze(message)

        assert result.score < 0.3, f"Expected score < 0.3, got {result.score}"

    @pytest.mark.asyncio
    async def test_moderate_negative_keywords_reduce_score(self) -> None:
        """Test that moderate negative keywords reduce score."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="I'm frustrated with this")
        result = await analyzer.analyze(message)

        # Moderate negative should reduce from 0.5 but not as much as strong
        assert result.score < 0.5, f"Expected score < 0.5, got {result.score}"

    @pytest.mark.asyncio
    async def test_neutral_message_produces_baseline_score(self) -> None:
        """Test that neutral message produces score around 0.5."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="I have a question about my account")
        result = await analyzer.analyze(message)

        # Neutral should be around 0.5 (within tolerance)
        assert 0.4 <= result.score <= 0.6, f"Expected score ~0.5, got {result.score}"

    @pytest.mark.asyncio
    async def test_positive_keywords_increase_score(self) -> None:
        """Test that positive keywords increase score above baseline."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Thank you so much, this is great!")
        result = await analyzer.analyze(message)

        assert result.score > 0.5, f"Expected score > 0.5, got {result.score}"

    @pytest.mark.asyncio
    async def test_multiple_negative_keywords_cumulative(self) -> None:
        """Test that multiple negative keywords have cumulative effect."""
        analyzer = RuleBasedAnalyzer()

        # Single negative keyword
        msg1 = Message(speaker=MessageSpeaker.USER, content="This is terrible")
        result1 = await analyzer.analyze(msg1)

        # Multiple negative keywords
        msg2 = Message(speaker=MessageSpeaker.USER, content="This is terrible, awful, and horrible!")
        result2 = await analyzer.analyze(msg2)

        assert result2.score < result1.score, "Multiple negatives should have lower score"

    @pytest.mark.asyncio
    async def test_frustration_keywords_reduce_score(self) -> None:
        """Test that frustration keywords reduce score."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="This is not working again, it failed")
        result = await analyzer.analyze(message)

        assert result.score < 0.5, f"Expected score < 0.5, got {result.score}"


class TestFeatureExtraction:
    """Tests for extract_features() method."""

    def test_extract_features_returns_sentiment_features(self) -> None:
        """Test that extract_features returns SentimentFeatures object."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello world")
        features = analyzer.extract_features(message)

        assert isinstance(features, SentimentFeatures)

    def test_extract_features_counts_negative_keywords(self) -> None:
        """Test that negative keywords are counted correctly."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="This is terrible and awful")
        features = analyzer.extract_features(message)

        assert features.negative_keyword_count >= 2

    def test_extract_features_counts_positive_keywords(self) -> None:
        """Test that positive keywords are counted correctly."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Great work, thank you!")
        features = analyzer.extract_features(message)

        assert features.positive_keyword_count >= 2

    def test_extract_features_counts_exclamation_marks(self) -> None:
        """Test that exclamation marks are counted."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Help me!!! This is urgent!!!")
        features = analyzer.extract_features(message)

        assert features.exclamation_count >= 6

    def test_extract_features_counts_question_marks(self) -> None:
        """Test that question marks are counted."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Why??? What happened???")
        features = analyzer.extract_features(message)

        assert features.question_count >= 6

    def test_extract_features_calculates_caps_ratio(self) -> None:
        """Test that caps ratio is calculated correctly."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="WHY IS THIS NOT WORKING")
        features = analyzer.extract_features(message)

        # Should have high caps ratio (most letters are uppercase)
        assert features.caps_ratio > 0.8

    def test_extract_features_low_caps_ratio(self) -> None:
        """Test low caps ratio for normal text."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="this is normal text")
        features = analyzer.extract_features(message)

        assert features.caps_ratio < 0.1

    def test_extract_features_detects_repeated_chars(self) -> None:
        """Test detection of repeated characters."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Noooooo this is sooo bad")
        features = analyzer.extract_features(message)

        assert features.repeated_chars is True

    def test_extract_features_no_repeated_chars(self) -> None:
        """Test no repeated chars in normal text."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="This is normal text")
        features = analyzer.extract_features(message)

        assert features.repeated_chars is False

    def test_extract_features_message_length(self) -> None:
        """Test that message length is set correctly."""
        analyzer = RuleBasedAnalyzer()
        content = "Hello world"
        message = Message(speaker=MessageSpeaker.USER, content=content)
        features = analyzer.extract_features(message)

        assert features.message_length == len(content)


class TestEscalationDecision:
    """Tests for should_escalate decision."""

    @pytest.mark.asyncio
    async def test_escalate_when_score_below_threshold(self) -> None:
        """Test that should_escalate is True when score < threshold."""
        analyzer = RuleBasedAnalyzer(threshold=0.3)
        message = Message(speaker=MessageSpeaker.USER, content="This is terrible and awful!")
        result = await analyzer.analyze(message)

        assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_no_escalate_when_score_above_threshold(self) -> None:
        """Test that should_escalate is False when score >= threshold."""
        analyzer = RuleBasedAnalyzer(threshold=0.3)
        message = Message(speaker=MessageSpeaker.USER, content="Thank you for your help!")
        result = await analyzer.analyze(message)

        assert result.should_escalate is False

    @pytest.mark.asyncio
    async def test_custom_threshold_affects_escalation(self) -> None:
        """Test that custom threshold affects escalation decision."""
        # With higher threshold, more messages trigger escalation
        analyzer = RuleBasedAnalyzer(threshold=0.6)
        message = Message(speaker=MessageSpeaker.USER, content="I have a question")
        result = await analyzer.analyze(message)

        # Neutral message (0.5) should trigger escalation with 0.6 threshold
        assert result.should_escalate is True


class TestSentimentResultFields:
    """Tests for SentimentResult field values."""

    @pytest.mark.asyncio
    async def test_result_has_score(self) -> None:
        """Test that result has score field."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")
        result = await analyzer.analyze(message)

        assert hasattr(result, "score")
        assert isinstance(result.score, float)

    @pytest.mark.asyncio
    async def test_result_has_frustration_level(self) -> None:
        """Test that result has frustration_level field."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")
        result = await analyzer.analyze(message)

        assert hasattr(result, "frustration_level")
        assert isinstance(result.frustration_level, float)

    @pytest.mark.asyncio
    async def test_result_tier_is_rule_based(self) -> None:
        """Test that tier_used is 'rule_based'."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")
        result = await analyzer.analyze(message)

        assert result.tier_used == "rule_based"

    @pytest.mark.asyncio
    async def test_result_has_processing_time(self) -> None:
        """Test that result includes processing_time_ms."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")
        result = await analyzer.analyze(message)

        assert hasattr(result, "processing_time_ms")
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_score_clamped_to_valid_range(self) -> None:
        """Test that score is clamped between 0.0 and 1.0."""
        analyzer = RuleBasedAnalyzer()
        # Many negative keywords that might push score below 0
        message = Message(
            speaker=MessageSpeaker.USER,
            content="terrible awful horrible worst hate useless stupid ridiculous unacceptable"
        )
        result = await analyzer.analyze(message)

        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_score_clamped_max(self) -> None:
        """Test that score doesn't exceed 1.0."""
        analyzer = RuleBasedAnalyzer()
        # Many positive keywords
        message = Message(
            speaker=MessageSpeaker.USER,
            content="thank you great awesome excellent helpful amazing perfect wonderful love appreciate"
        )
        result = await analyzer.analyze(message)

        assert result.score <= 1.0


class TestCapsAndPunctuation:
    """Tests for caps lock and punctuation handling."""

    @pytest.mark.asyncio
    async def test_all_caps_reduces_score(self) -> None:
        """Test that ALL CAPS message reduces score."""
        analyzer = RuleBasedAnalyzer()

        # Normal case
        msg_normal = Message(speaker=MessageSpeaker.USER, content="I need help now")
        result_normal = await analyzer.analyze(msg_normal)

        # ALL CAPS
        msg_caps = Message(speaker=MessageSpeaker.USER, content="I NEED HELP NOW")
        result_caps = await analyzer.analyze(msg_caps)

        assert result_caps.score < result_normal.score, "ALL CAPS should reduce score"

    @pytest.mark.asyncio
    async def test_excessive_punctuation_reduces_score(self) -> None:
        """Test that excessive punctuation reduces score."""
        analyzer = RuleBasedAnalyzer()

        # Normal punctuation
        msg_normal = Message(speaker=MessageSpeaker.USER, content="Help me!")
        result_normal = await analyzer.analyze(msg_normal)

        # Excessive punctuation
        msg_excessive = Message(speaker=MessageSpeaker.USER, content="Help me!!!!!!")
        result_excessive = await analyzer.analyze(msg_excessive)

        assert result_excessive.score < result_normal.score, "Excessive punctuation should reduce score"


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_analyze_under_10ms(self) -> None:
        """Test that analysis completes in under 10ms."""
        analyzer = RuleBasedAnalyzer()
        message = Message(
            speaker=MessageSpeaker.USER,
            content="This is a test message with some words"
        )

        start = time.perf_counter()
        await analyzer.analyze(message)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"Analysis took {elapsed_ms:.2f}ms, expected < 10ms"

    @pytest.mark.asyncio
    async def test_processing_time_in_result(self) -> None:
        """Test that processing_time_ms is recorded in result."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Test message")
        result = await analyzer.analyze(message)

        assert result.processing_time_ms > 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_message(self) -> None:
        """Test handling of empty message content."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="")
        result = await analyzer.analyze(message)

        # Empty message should return baseline score
        assert 0.4 <= result.score <= 0.6

    @pytest.mark.asyncio
    async def test_whitespace_only_message(self) -> None:
        """Test handling of whitespace-only message."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="   ")
        result = await analyzer.analyze(message)

        # Whitespace should return baseline score
        assert 0.4 <= result.score <= 0.6

    @pytest.mark.asyncio
    async def test_special_characters_only(self) -> None:
        """Test handling of special characters only."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="@#$%^&*()")
        result = await analyzer.analyze(message)

        # Should return baseline score
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_very_long_message(self) -> None:
        """Test handling of very long message."""
        analyzer = RuleBasedAnalyzer()
        long_content = "word " * 1000  # 5000 characters
        message = Message(speaker=MessageSpeaker.USER, content=long_content)

        start = time.perf_counter()
        result = await analyzer.analyze(message)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should still complete quickly
        assert elapsed_ms < 50, f"Long message took {elapsed_ms:.2f}ms"
        assert 0.0 <= result.score <= 1.0


class TestHistoryContext:
    """Tests for conversation history handling."""

    @pytest.mark.asyncio
    async def test_analyze_with_history(self) -> None:
        """Test that analyze accepts history parameter."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")
        history = [
            Message(speaker=MessageSpeaker.USER, content="Previous message"),
            Message(speaker=MessageSpeaker.AI, content="AI response"),
        ]

        # Should not raise exception
        result = await analyzer.analyze(message, history=history)
        assert isinstance(result, SentimentResult)

    @pytest.mark.asyncio
    async def test_analyze_without_history(self) -> None:
        """Test that analyze works without history."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Hello")

        result = await analyzer.analyze(message)
        assert isinstance(result, SentimentResult)
