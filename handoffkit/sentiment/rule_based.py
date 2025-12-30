"""Rule-based sentiment analyzer (Tier 1)."""

import re
import time
from typing import Any, Optional

from handoffkit.core.types import Message, SentimentResult
from handoffkit.sentiment.models import SentimentFeatures
from handoffkit.utils.logging import get_logger


class RuleBasedAnalyzer:
    """Fast rule-based sentiment analysis using keyword scoring.

    Features:
    - Keyword presence scoring (positive/negative/frustration)
    - Punctuation analysis (exclamation marks, caps)
    - Pattern detection (repeated chars, profanity)

    Target: <10ms evaluation time.
    """

    # Strong negative keywords (-0.3 weight each)
    STRONG_NEGATIVE_KEYWORDS = [
        "terrible", "awful", "horrible", "worst", "hate",
        "useless", "stupid", "ridiculous", "unacceptable",
    ]

    # Moderate negative keywords (-0.15 weight each)
    MODERATE_NEGATIVE_KEYWORDS = [
        "angry", "frustrated", "annoyed", "upset",
        "disappointed", "waste",
    ]

    # Positive sentiment keywords (+0.2 weight each)
    POSITIVE_KEYWORDS = [
        "thank", "great", "awesome", "excellent", "helpful",
        "amazing", "perfect", "wonderful", "love", "appreciate",
    ]

    # Frustration-specific keywords (-0.1 weight each)
    FRUSTRATION_KEYWORDS = [
        "again", "already", "still", "not working", "doesn't work",
        "broken", "wrong", "failed", "error", "problem",
    ]

    # Default keyword weights
    DEFAULT_WEIGHTS = {
        "strong_negative": -0.3,
        "moderate_negative": -0.15,
        "positive": 0.2,
        "frustration": -0.1,
    }

    def __init__(
        self,
        threshold: float = 0.3,
        weights: Optional[dict[str, float]] = None,
        domain_keywords: Optional[list[str]] = None,
        domain_amplifier: float = 1.5,
        degradation_tracker: Optional[Any] = None,
    ) -> None:
        """Initialize the rule-based analyzer.

        Args:
            threshold: Score below which should_escalate is True (default 0.3).
            weights: Custom keyword weights dict (optional).
            domain_keywords: Domain-specific keywords with amplified weight (optional).
            domain_amplifier: Multiplier for domain keyword impact (default 1.5).
            degradation_tracker: Optional DegradationTracker instance for trend analysis.
        """
        self._threshold = threshold
        self._weights = {**self.DEFAULT_WEIGHTS, **(weights or {})}
        self._domain_keywords = domain_keywords or []
        self._domain_amplifier = domain_amplifier
        self._degradation_tracker = degradation_tracker

        # Pre-compile regex patterns for performance
        self._strong_negative_pattern = self._compile_pattern(self.STRONG_NEGATIVE_KEYWORDS)
        self._moderate_negative_pattern = self._compile_pattern(self.MODERATE_NEGATIVE_KEYWORDS)
        self._positive_pattern = self._compile_pattern(self.POSITIVE_KEYWORDS)
        self._frustration_pattern = self._compile_pattern(self.FRUSTRATION_KEYWORDS)

        # For backward compatibility - combined negative pattern
        self._negative_pattern = self._compile_pattern(
            self.STRONG_NEGATIVE_KEYWORDS + self.MODERATE_NEGATIVE_KEYWORDS
        )

        # Pattern for repeated characters (3+ of same char)
        self._repeated_chars_pattern = re.compile(r"(.)\1{2,}")

        # Pattern for excessive punctuation (3+ consecutive ! or ?)
        self._excessive_punct_pattern = re.compile(r"[!?]{3,}")

        # Domain keywords pattern if provided
        if self._domain_keywords:
            self._domain_pattern = self._compile_pattern(self._domain_keywords)
        else:
            self._domain_pattern = None

        # Initialize logger
        self._logger = get_logger("sentiment.rule_based")

    def _compile_pattern(self, keywords: list[str]) -> re.Pattern[str]:
        """Compile keywords into a regex pattern with word boundaries."""
        if not keywords:
            # Return pattern that matches nothing
            return re.compile(r"(?!)")
        escaped = [re.escape(k) for k in keywords]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def _count_matches(self, pattern: re.Pattern[str], text: str) -> int:
        """Count pattern matches in text."""
        return len(pattern.findall(text))

    def _count_caps_words(self, text: str) -> int:
        """Count ALL CAPS words (2+ characters, entirely uppercase).

        Args:
            text: The text to analyze.

        Returns:
            Number of ALL CAPS words found.
        """
        words = re.findall(r"\b[A-Za-z]+\b", text)
        return sum(1 for word in words if len(word) >= 2 and word.isupper())

    def extract_features(self, message: Message) -> SentimentFeatures:
        """Extract sentiment features from a message.

        Args:
            message: The message to analyze.

        Returns:
            SentimentFeatures with extracted feature values.
        """
        content = message.content

        # Count keyword matches
        strong_negative_count = self._count_matches(self._strong_negative_pattern, content)
        moderate_negative_count = self._count_matches(self._moderate_negative_pattern, content)
        positive_count = self._count_matches(self._positive_pattern, content)
        frustration_count = self._count_matches(self._frustration_pattern, content)

        # Total negative count for backward compatibility
        negative_count = strong_negative_count + moderate_negative_count

        # Count punctuation
        exclamation_count = content.count("!")
        question_count = content.count("?")

        # Calculate caps ratio (uppercase letters / total letters)
        letters = [c for c in content if c.isalpha()]
        if letters:
            caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        else:
            caps_ratio = 0.0

        # Detect repeated characters (3+ consecutive same char)
        repeated_chars = bool(self._repeated_chars_pattern.search(content))

        # Count ALL CAPS words (Story 2.6)
        caps_word_count = self._count_caps_words(content)

        # Count excessive punctuation patterns (3+ consecutive ! or ?)
        excessive_punctuation_count = len(self._excessive_punct_pattern.findall(content))

        # Message length
        message_length = len(content)

        return SentimentFeatures(
            negative_keyword_count=negative_count,
            positive_keyword_count=positive_count,
            frustration_keyword_count=frustration_count,
            exclamation_count=exclamation_count,
            question_count=question_count,
            caps_ratio=caps_ratio,
            caps_word_count=caps_word_count,
            excessive_punctuation_count=excessive_punctuation_count,
            repeated_chars=repeated_chars,
            contains_profanity=False,  # Not implemented for Tier 1
            message_length=message_length,
            message_position=0,  # Would need history context
            conversation_length=0,  # Would need history context
            recent_negative_trend=0.0,  # Would need history context
        )

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using rule-based approach.

        Args:
            message: The current message to analyze.
            history: Previous messages in the conversation (optional).

        Returns:
            SentimentResult with score, frustration_level, and escalation decision.
        """
        start_time = time.perf_counter()

        # Log evaluation start
        message_preview = (
            message.content[:50] + "..."
            if len(message.content) > 50
            else message.content
        )
        self._logger.debug(
            "Evaluating sentiment (rule-based)",
            extra={
                "message_preview": message_preview,
                "tier": "rule_based",
            },
        )

        # Track sentiment history if degradation tracker is enabled
        degradation_detected = False
        if self._degradation_tracker and history:
            # Analyze historical user messages and track scores
            for hist_msg in history:
                if hist_msg.speaker == "user" or hist_msg.speaker == "USER":
                    hist_features = self.extract_features(hist_msg)
                    hist_score = self._calculate_score(hist_msg, hist_features)
                    self._degradation_tracker.track_score(hist_score)

        # Extract features
        features = self.extract_features(message)

        # Update contextual features if history provided
        if history is not None:
            features.conversation_length = len(history) + 1
            features.message_position = len(history)

        self._logger.debug(
            "Extracted sentiment features",
            extra={
                "negative_count": features.negative_keyword_count,
                "positive_count": features.positive_keyword_count,
                "frustration_count": features.frustration_keyword_count,
                "caps_ratio": round(features.caps_ratio, 2),
                "caps_word_count": features.caps_word_count,
                "excessive_punctuation_count": features.excessive_punctuation_count,
                "exclamation_count": features.exclamation_count,
                "repeated_chars": features.repeated_chars,
            },
        )

        # Calculate score
        score = self._calculate_score(message, features)

        # Track current message score if degradation tracker enabled
        if self._degradation_tracker:
            self._degradation_tracker.track_score(score)

            # Check for degradation
            degradation_result = self._degradation_tracker.check_degradation()
            degradation_detected = degradation_result.is_degrading

            # Update contextual features with degradation trend
            if degradation_result.window_size > 0:
                features.recent_negative_trend = degradation_result.trend_value

        # Calculate frustration level (normalized from features) - Story 2.6 enhanced
        frustration_level = min(1.0, (
            features.frustration_keyword_count * 0.2 +
            features.negative_keyword_count * 0.15 +
            features.caps_word_count * 0.1 +  # Story 2.6: per-word caps contribution
            features.excessive_punctuation_count * 0.05 +  # Story 2.6: per-pattern contribution
            (0.1 if features.repeated_chars else 0.0)
        ))

        # Determine escalation
        should_escalate = score < self._threshold or degradation_detected

        # Calculate processing time
        processing_time_ms = (time.perf_counter() - start_time) * 1000

        self._logger.debug(
            "Sentiment analysis complete",
            extra={
                "score": round(score, 3),
                "frustration_level": round(frustration_level, 3),
                "should_escalate": should_escalate,
                "degradation_detected": degradation_detected,
                "threshold": self._threshold,
                "processing_time_ms": round(processing_time_ms, 3),
                "tier": "rule_based",
            },
        )

        return SentimentResult(
            score=score,
            frustration_level=frustration_level,
            should_escalate=should_escalate,
            degradation_detected=degradation_detected,
            tier_used="rule_based",
            processing_time_ms=processing_time_ms,
        )

    def _calculate_score(self, message: Message, features: SentimentFeatures) -> float:
        """Calculate sentiment score from features.

        Args:
            message: The message being analyzed.
            features: Extracted sentiment features.

        Returns:
            Sentiment score (0.0-1.0).
        """
        content = message.content

        # Calculate base score starting from neutral 0.5
        score = 0.5

        # Count strong vs moderate negative separately for scoring
        strong_neg_count = self._count_matches(self._strong_negative_pattern, content)
        moderate_neg_count = self._count_matches(self._moderate_negative_pattern, content)

        # Apply keyword weights
        score += features.positive_keyword_count * self._weights["positive"]
        score -= strong_neg_count * abs(self._weights["strong_negative"])
        score -= moderate_neg_count * abs(self._weights["moderate_negative"])
        score -= features.frustration_keyword_count * abs(self._weights["frustration"])

        # Apply modifiers for caps and punctuation (Story 2.6 enhancement)
        # Per-word caps penalty: -0.1 per ALL CAPS word, max -0.3
        caps_penalty = min(features.caps_word_count * 0.1, 0.3)
        score -= caps_penalty

        # Per-pattern excessive punctuation penalty: -0.05 per 3+ consecutive !/?
        punct_penalty = min(features.excessive_punctuation_count * 0.05, 0.2)
        score -= punct_penalty

        # Domain keyword amplification
        if self._domain_pattern:
            domain_matches = self._count_matches(self._domain_pattern, content)
            # Domain keywords amplify the negative direction
            score -= domain_matches * 0.1 * self._domain_amplifier

        # Clamp to valid range [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        return score
