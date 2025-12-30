"""Tests for conversation degradation tracking (Story 2.7)."""

import time

import pytest

from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.sentiment.degradation import DegradationTracker
from handoffkit.sentiment.models import DegradationResult


class TestDegradationTracker:
    """Tests for DegradationTracker class."""

    def test_tracker_initializes(self) -> None:
        """Test tracker can be instantiated with default parameters."""
        tracker = DegradationTracker()
        assert tracker is not None

    def test_tracker_accepts_custom_window_size(self) -> None:
        """Test tracker accepts custom window_size parameter."""
        tracker = DegradationTracker(window_size=10)
        assert tracker._window_size == 10

    def test_tracker_accepts_custom_threshold(self) -> None:
        """Test tracker accepts custom threshold parameter."""
        tracker = DegradationTracker(threshold=0.4)
        assert tracker._threshold == 0.4

    def test_track_score_adds_to_window(self) -> None:
        """Test that track_score adds scores to internal window."""
        tracker = DegradationTracker()
        tracker.track_score(0.5)
        scores = tracker.get_recent_scores()
        assert len(scores) == 1
        assert scores[0] == 0.5

    def test_track_multiple_scores(self) -> None:
        """Test tracking multiple scores."""
        tracker = DegradationTracker()
        tracker.track_score(0.7)
        tracker.track_score(0.6)
        tracker.track_score(0.5)
        scores = tracker.get_recent_scores()
        assert len(scores) == 3
        assert scores == [0.7, 0.6, 0.5]

    def test_rolling_window_limits_to_window_size(self) -> None:
        """Test that rolling window limits to window_size (AC #2)."""
        tracker = DegradationTracker(window_size=5)
        for score in [0.7, 0.6, 0.5, 0.4, 0.3, 0.2]:
            tracker.track_score(score)
        scores = tracker.get_recent_scores()
        # Should only keep last 5 scores
        assert len(scores) == 5
        assert scores == [0.6, 0.5, 0.4, 0.3, 0.2]

    def test_clear_resets_tracking(self) -> None:
        """Test that clear() resets tracking for new conversations."""
        tracker = DegradationTracker()
        tracker.track_score(0.5)
        tracker.track_score(0.4)
        tracker.clear()
        scores = tracker.get_recent_scores()
        assert len(scores) == 0

    def test_calculate_trend_empty_window(self) -> None:
        """Test calculate_trend with empty window."""
        tracker = DegradationTracker()
        trend = tracker.calculate_trend()
        assert trend == 0.0

    def test_calculate_trend_single_score(self) -> None:
        """Test calculate_trend with single score."""
        tracker = DegradationTracker()
        tracker.track_score(0.5)
        trend = tracker.calculate_trend()
        assert trend == 0.0

    def test_calculate_trend_degrading_sentiment(self) -> None:
        """Test calculate_trend detects degrading sentiment (AC #1)."""
        tracker = DegradationTracker()
        # Simulate degrading conversation: 0.7 → 0.3
        for score in [0.7, 0.6, 0.5, 0.4, 0.3]:
            tracker.track_score(score)
        trend = tracker.calculate_trend()
        # Trend = first_score - last_score = 0.7 - 0.3 = 0.4
        assert pytest.approx(trend, abs=1e-9) == 0.4

    def test_calculate_trend_stable_sentiment(self) -> None:
        """Test calculate_trend with stable sentiment (AC #3)."""
        tracker = DegradationTracker()
        for score in [0.5, 0.5, 0.5, 0.5, 0.5]:
            tracker.track_score(score)
        trend = tracker.calculate_trend()
        # Trend = 0.5 - 0.5 = 0.0
        assert trend == 0.0

    def test_calculate_trend_improving_sentiment(self) -> None:
        """Test calculate_trend with improving sentiment (AC #4)."""
        tracker = DegradationTracker()
        for score in [0.3, 0.4, 0.5, 0.6, 0.7]:
            tracker.track_score(score)
        trend = tracker.calculate_trend()
        # Trend = 0.3 - 0.7 = -0.4 (negative means improving)
        assert pytest.approx(trend, abs=1e-9) == -0.4

    def test_check_degradation_triggers_on_threshold(self) -> None:
        """Test check_degradation triggers when trend > threshold (AC #1)."""
        tracker = DegradationTracker(threshold=0.3)
        # Simulate degrading conversation: 0.7 → 0.3 (trend = 0.4)
        for score in [0.7, 0.6, 0.5, 0.4, 0.3]:
            tracker.track_score(score)
        result = tracker.check_degradation()
        assert isinstance(result, DegradationResult)
        assert result.is_degrading is True
        assert pytest.approx(result.trend_value, abs=1e-9) == 0.4
        assert result.window_size == 5
        assert result.scores == [0.7, 0.6, 0.5, 0.4, 0.3]

    def test_check_degradation_no_trigger_stable(self) -> None:
        """Test check_degradation doesn't trigger on stable sentiment (AC #3)."""
        tracker = DegradationTracker(threshold=0.3)
        for score in [0.5, 0.5, 0.5, 0.5, 0.5]:
            tracker.track_score(score)
        result = tracker.check_degradation()
        assert result.is_degrading is False
        assert result.trend_value == 0.0

    def test_check_degradation_no_trigger_improving(self) -> None:
        """Test check_degradation doesn't trigger on improving sentiment (AC #4)."""
        tracker = DegradationTracker(threshold=0.3)
        for score in [0.3, 0.4, 0.5, 0.6, 0.7]:
            tracker.track_score(score)
        result = tracker.check_degradation()
        assert result.is_degrading is False
        assert pytest.approx(result.trend_value, abs=1e-9) == -0.4

    def test_check_degradation_fewer_than_window_size(self) -> None:
        """Test check_degradation with fewer than window_size messages (AC #5)."""
        tracker = DegradationTracker(window_size=5, threshold=0.3)
        # Only 3 messages
        for score in [0.7, 0.5, 0.3]:
            tracker.track_score(score)
        result = tracker.check_degradation()
        # Should still calculate: 0.7 - 0.3 = 0.4 > 0.3
        assert result.is_degrading is True
        assert pytest.approx(result.trend_value, abs=1e-9) == 0.4
        assert result.window_size == 3

    def test_degradation_result_has_required_fields(self) -> None:
        """Test DegradationResult has all required fields (AC #1)."""
        tracker = DegradationTracker()
        tracker.track_score(0.5)
        tracker.track_score(0.3)
        result = tracker.check_degradation()
        assert hasattr(result, 'is_degrading')
        assert hasattr(result, 'trend_value')
        assert hasattr(result, 'window_size')
        assert hasattr(result, 'scores')


class TestDegradationPerformance:
    """Performance tests for degradation tracking (AC #6)."""

    def test_tracker_operations_are_fast(self) -> None:
        """Test that tracker operations complete quickly."""
        tracker = DegradationTracker()

        start = time.perf_counter()
        for i in range(100):
            tracker.track_score(0.5 - i * 0.001)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should be extremely fast (well under 10ms for 100 ops)
        assert elapsed_ms < 10

    def test_check_degradation_performance(self) -> None:
        """Test check_degradation completes quickly."""
        tracker = DegradationTracker()
        for score in [0.7, 0.6, 0.5, 0.4, 0.3]:
            tracker.track_score(score)

        start = time.perf_counter()
        result = tracker.check_degradation()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should be extremely fast (well under 1ms)
        assert elapsed_ms < 1
        assert result is not None


class TestDegradationResult:
    """Tests for DegradationResult model."""

    def test_degradation_result_can_be_created(self) -> None:
        """Test DegradationResult can be instantiated."""
        result = DegradationResult(
            is_degrading=True,
            trend_value=0.4,
            window_size=5,
            scores=[0.7, 0.6, 0.5, 0.4, 0.3],
        )
        assert result.is_degrading is True
        assert result.trend_value == 0.4
        assert result.window_size == 5
        assert len(result.scores) == 5
