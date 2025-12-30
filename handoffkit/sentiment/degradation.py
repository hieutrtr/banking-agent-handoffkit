"""Conversation degradation tracking for sentiment analysis."""

from collections import deque

from handoffkit.sentiment.models import DegradationResult
from handoffkit.utils.logging import get_logger


class DegradationTracker:
    """Track conversation sentiment degradation over a rolling window.

    Features:
    - Rolling window of recent sentiment scores
    - Trend calculation (first_score - last_score)
    - Configurable threshold for degradation detection

    Args:
        window_size: Number of messages to track (default 5)
        threshold: Degradation threshold (default 0.3)
    """

    def __init__(self, window_size: int = 5, threshold: float = 0.3) -> None:
        """Initialize the degradation tracker.

        Args:
            window_size: Number of messages to track in rolling window.
            threshold: Trend threshold above which degradation triggers.
        """
        self._window_size = window_size
        self._threshold = threshold
        self._scores: deque[float] = deque(maxlen=window_size)
        self._logger = get_logger("sentiment.degradation")

    def track_score(self, score: float) -> None:
        """Add a sentiment score to the rolling window.

        Args:
            score: Sentiment score to track (0.0-1.0).
        """
        self._scores.append(score)
        self._logger.debug(
            "Tracked sentiment score",
            extra={
                "score": score,
                "window_size": len(self._scores),
                "max_window_size": self._window_size,
            },
        )

    def get_recent_scores(self) -> list[float]:
        """Get recent scores in the rolling window.

        Returns:
            List of recent scores (oldest to newest).
        """
        return list(self._scores)

    def clear(self) -> None:
        """Reset tracking for new conversations."""
        self._scores.clear()
        self._logger.debug("Cleared degradation tracker")

    def calculate_trend(self) -> float:
        """Calculate sentiment trend (positive = degrading, negative = improving).

        Trend is calculated as: first_score - last_score
        - Positive trend value = sentiment getting worse (degrading)
        - Negative trend value = sentiment improving
        - Zero = stable

        Returns:
            Trend value. Returns 0.0 if fewer than 2 scores.
        """
        if len(self._scores) < 2:
            return 0.0

        trend = self._scores[0] - self._scores[-1]

        self._logger.debug(
            "Calculated sentiment trend",
            extra={
                "trend": round(trend, 3),
                "first_score": self._scores[0],
                "last_score": self._scores[-1],
                "window_size": len(self._scores),
            },
        )

        return trend

    def check_degradation(self) -> DegradationResult:
        """Check if conversation is degrading.

        Returns:
            DegradationResult with degradation status and details.
        """
        trend = self.calculate_trend()
        is_degrading = trend > self._threshold

        result = DegradationResult(
            is_degrading=is_degrading,
            trend_value=trend,
            window_size=len(self._scores),
            scores=list(self._scores),
        )

        if is_degrading:
            self._logger.info(
                "Conversation degradation detected",
                extra={
                    "trend_value": round(trend, 3),
                    "threshold": self._threshold,
                    "window_size": len(self._scores),
                    "scores": [round(s, 3) for s in self._scores],
                },
            )
        else:
            self._logger.debug(
                "No degradation detected",
                extra={
                    "trend_value": round(trend, 3),
                    "threshold": self._threshold,
                },
            )

        return result
