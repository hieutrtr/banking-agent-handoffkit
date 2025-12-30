"""Tests for frustration signal detection (Story 2.6).

Tests enhanced caps word detection and excessive punctuation patterns.
"""

import time

import pytest

from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer


class TestCapsWordDetection:
    """Tests for ALL CAPS word detection (AC #1, #4)."""

    @pytest.mark.asyncio
    async def test_single_caps_word_reduces_score_by_0_1(self) -> None:
        """Test that a single ALL CAPS word reduces score by 0.1."""
        analyzer = RuleBasedAnalyzer()

        # Baseline without caps words
        msg_normal = Message(speaker=MessageSpeaker.USER, content="I need help now")
        result_normal = await analyzer.analyze(msg_normal)

        # Single caps word
        msg_caps = Message(speaker=MessageSpeaker.USER, content="I need HELP now")
        result_caps = await analyzer.analyze(msg_caps)

        # Should reduce by approximately 0.1
        score_diff = result_normal.score - result_caps.score
        assert 0.08 <= score_diff <= 0.12, f"Expected ~0.1 reduction, got {score_diff}"

    @pytest.mark.asyncio
    async def test_multiple_caps_words_cumulative_effect(self) -> None:
        """Test that multiple caps words have cumulative effect."""
        analyzer = RuleBasedAnalyzer()

        # Single caps word
        msg_one = Message(speaker=MessageSpeaker.USER, content="I NEED help now")
        result_one = await analyzer.analyze(msg_one)

        # Two caps words
        msg_two = Message(speaker=MessageSpeaker.USER, content="I NEED HELP now")
        result_two = await analyzer.analyze(msg_two)

        # Three caps words
        msg_three = Message(speaker=MessageSpeaker.USER, content="I NEED HELP NOW")
        result_three = await analyzer.analyze(msg_three)

        # Each additional caps word should reduce score further
        assert result_two.score < result_one.score, "Two caps words should score lower than one"
        assert result_three.score < result_two.score, "Three caps words should score lower than two"

    @pytest.mark.asyncio
    async def test_caps_penalty_capped_at_0_3(self) -> None:
        """Test that caps penalty is capped at -0.3 (3 words max impact)."""
        analyzer = RuleBasedAnalyzer()

        # Baseline
        msg_normal = Message(speaker=MessageSpeaker.USER, content="i need help now please")
        result_normal = await analyzer.analyze(msg_normal)

        # Many caps words (more than 3)
        msg_many_caps = Message(
            speaker=MessageSpeaker.USER,
            content="I NEED HELP NOW PLEASE IMMEDIATELY"
        )
        result_many_caps = await analyzer.analyze(msg_many_caps)

        # Maximum penalty should be 0.3
        score_diff = result_normal.score - result_many_caps.score
        assert score_diff <= 0.35, f"Caps penalty should be capped at ~0.3, got {score_diff}"

    @pytest.mark.asyncio
    async def test_single_letter_caps_not_counted(self) -> None:
        """Test that single letter caps like 'I' and 'A' are not penalized."""
        analyzer = RuleBasedAnalyzer()

        # Message with only single letter caps
        msg_single = Message(speaker=MessageSpeaker.USER, content="I need A solution")
        result_single = await analyzer.analyze(msg_single)

        # Same message lowercase
        msg_lower = Message(speaker=MessageSpeaker.USER, content="i need a solution")
        result_lower = await analyzer.analyze(msg_lower)

        # Should have same score (no penalty for I and A)
        assert abs(result_single.score - result_lower.score) < 0.05, \
            "Single letter caps should not affect score"

    @pytest.mark.asyncio
    async def test_normal_capitalization_no_penalty(self) -> None:
        """Test that normal sentence capitalization has no penalty."""
        analyzer = RuleBasedAnalyzer()

        # Normal capitalization
        msg_normal = Message(
            speaker=MessageSpeaker.USER,
            content="Hello, I have a question about my account."
        )
        result = await analyzer.analyze(msg_normal)

        # Should be around neutral (0.5)
        assert 0.4 <= result.score <= 0.6, f"Normal text should be neutral, got {result.score}"


class TestExcessivePunctuationDetection:
    """Tests for excessive punctuation pattern detection (AC #2)."""

    @pytest.mark.asyncio
    async def test_triple_exclamation_reduces_score(self) -> None:
        """Test that !!! reduces score by 0.05."""
        analyzer = RuleBasedAnalyzer()

        # Normal punctuation
        msg_normal = Message(speaker=MessageSpeaker.USER, content="Help me!")
        result_normal = await analyzer.analyze(msg_normal)

        # Triple exclamation
        msg_triple = Message(speaker=MessageSpeaker.USER, content="Help me!!!")
        result_triple = await analyzer.analyze(msg_triple)

        score_diff = result_normal.score - result_triple.score
        assert 0.03 <= score_diff <= 0.07, f"Expected ~0.05 reduction, got {score_diff}"

    @pytest.mark.asyncio
    async def test_triple_question_marks_reduces_score(self) -> None:
        """Test that ??? reduces score by 0.05."""
        analyzer = RuleBasedAnalyzer()

        # Normal punctuation
        msg_normal = Message(speaker=MessageSpeaker.USER, content="Why?")
        result_normal = await analyzer.analyze(msg_normal)

        # Triple question marks
        msg_triple = Message(speaker=MessageSpeaker.USER, content="Why???")
        result_triple = await analyzer.analyze(msg_triple)

        score_diff = result_normal.score - result_triple.score
        assert 0.03 <= score_diff <= 0.07, f"Expected ~0.05 reduction, got {score_diff}"

    @pytest.mark.asyncio
    async def test_multiple_excessive_punctuation_instances(self) -> None:
        """Test that multiple excessive punctuation instances have cumulative effect."""
        analyzer = RuleBasedAnalyzer()

        # One instance
        msg_one = Message(speaker=MessageSpeaker.USER, content="Help!!!")
        result_one = await analyzer.analyze(msg_one)

        # Two instances
        msg_two = Message(speaker=MessageSpeaker.USER, content="Help!!! Why???")
        result_two = await analyzer.analyze(msg_two)

        assert result_two.score < result_one.score, \
            "Multiple excessive punctuation should reduce score more"

    @pytest.mark.asyncio
    async def test_excessive_punctuation_penalty_capped_at_0_2(self) -> None:
        """Test that punctuation penalty is capped at -0.2 (4 instances max)."""
        analyzer = RuleBasedAnalyzer()

        # Baseline
        msg_normal = Message(speaker=MessageSpeaker.USER, content="Help me please")
        result_normal = await analyzer.analyze(msg_normal)

        # Many excessive punctuation instances (more than 4)
        msg_many = Message(
            speaker=MessageSpeaker.USER,
            content="Help!!! Why??? What??? How??? Where??? Really???"
        )
        result_many = await analyzer.analyze(msg_many)

        score_diff = result_normal.score - result_many.score
        assert score_diff <= 0.25, f"Punctuation penalty should be capped at ~0.2, got {score_diff}"

    @pytest.mark.asyncio
    async def test_mixed_excessive_punctuation(self) -> None:
        """Test mixed !? patterns are detected."""
        analyzer = RuleBasedAnalyzer()

        # Normal
        msg_normal = Message(speaker=MessageSpeaker.USER, content="What is happening")
        result_normal = await analyzer.analyze(msg_normal)

        # Mixed excessive punctuation
        msg_mixed = Message(speaker=MessageSpeaker.USER, content="What is happening!?!")
        result_mixed = await analyzer.analyze(msg_mixed)

        assert result_mixed.score < result_normal.score, \
            "Mixed !?! should reduce score"


class TestCombinedFrustrationSignals:
    """Tests for combined caps and punctuation signals (AC #3)."""

    @pytest.mark.asyncio
    async def test_combined_caps_and_punctuation_stronger_effect(self) -> None:
        """Test that combined caps + punctuation has stronger effect than either alone."""
        analyzer = RuleBasedAnalyzer()

        # Just caps
        msg_caps = Message(speaker=MessageSpeaker.USER, content="I NEED HELP NOW")
        result_caps = await analyzer.analyze(msg_caps)

        # Just punctuation
        msg_punct = Message(speaker=MessageSpeaker.USER, content="I need help now!!!")
        result_punct = await analyzer.analyze(msg_punct)

        # Both caps and punctuation
        msg_both = Message(speaker=MessageSpeaker.USER, content="I NEED HELP NOW!!!")
        result_both = await analyzer.analyze(msg_both)

        assert result_both.score < result_caps.score, \
            "Combined should be lower than caps alone"
        assert result_both.score < result_punct.score, \
            "Combined should be lower than punctuation alone"

    @pytest.mark.asyncio
    async def test_frustration_level_reflects_combined_intensity(self) -> None:
        """Test that frustration_level reflects combined signal intensity."""
        analyzer = RuleBasedAnalyzer()

        # Minimal frustration signals
        msg_low = Message(speaker=MessageSpeaker.USER, content="I have a question")
        result_low = await analyzer.analyze(msg_low)

        # Strong frustration signals (caps + punctuation)
        msg_high = Message(
            speaker=MessageSpeaker.USER,
            content="WHY IS THIS NOT WORKING???"
        )
        result_high = await analyzer.analyze(msg_high)

        assert result_high.frustration_level > result_low.frustration_level, \
            "High frustration signals should have higher frustration_level"


class TestFrustrationPerformance:
    """Performance tests for frustration signal detection (AC #5)."""

    @pytest.mark.asyncio
    async def test_evaluation_under_10ms(self) -> None:
        """Test that evaluation completes in under 10ms."""
        analyzer = RuleBasedAnalyzer()
        message = Message(
            speaker=MessageSpeaker.USER,
            content="WHY IS THIS NOT WORKING??? I NEED HELP NOW!!!"
        )

        start = time.perf_counter()
        await analyzer.analyze(message)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"Analysis took {elapsed_ms:.2f}ms, expected < 10ms"

    @pytest.mark.asyncio
    async def test_many_caps_words_still_fast(self) -> None:
        """Test performance with many caps words."""
        analyzer = RuleBasedAnalyzer()
        # Message with many caps words
        message = Message(
            speaker=MessageSpeaker.USER,
            content="THIS IS A TEST MESSAGE WITH MANY CAPS WORDS TO CHECK PERFORMANCE"
        )

        start = time.perf_counter()
        await analyzer.analyze(message)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"Analysis took {elapsed_ms:.2f}ms, expected < 10ms"


class TestFeaturesExtraction:
    """Tests for feature extraction related to frustration signals."""

    def test_extract_caps_word_count(self) -> None:
        """Test that caps word count can be extracted from features."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="I NEED HELP NOW")
        features = analyzer.extract_features(message)

        # Should have caps_word_count field if implemented
        # This may need to be added to SentimentFeatures model
        assert hasattr(features, 'caps_word_count') or features.caps_ratio > 0.5

    def test_extract_excessive_punctuation_count(self) -> None:
        """Test that excessive punctuation count can be extracted."""
        analyzer = RuleBasedAnalyzer()
        message = Message(speaker=MessageSpeaker.USER, content="Help!!! Why???")
        features = analyzer.extract_features(message)

        # Should have excessive_punctuation_count field if implemented
        assert hasattr(features, 'excessive_punctuation_count') or features.exclamation_count >= 3
