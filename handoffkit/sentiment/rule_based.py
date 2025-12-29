"""Rule-based sentiment analyzer (Tier 1)."""

import re
from typing import Optional

from handoffkit.core.types import Message, SentimentResult
from handoffkit.sentiment.models import SentimentFeatures


class RuleBasedAnalyzer:
    """Fast rule-based sentiment analysis using keyword scoring.

    Features:
    - Keyword presence scoring (positive/negative/frustration)
    - Punctuation analysis (exclamation marks, caps)
    - Pattern detection (repeated chars, profanity)

    Target: <10ms evaluation time.
    """

    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = [
        "angry", "frustrated", "annoyed", "upset", "terrible",
        "awful", "horrible", "worst", "hate", "useless", "stupid",
        "ridiculous", "unacceptable", "disappointed", "waste",
    ]

    # Positive sentiment keywords
    POSITIVE_KEYWORDS = [
        "thank", "great", "awesome", "excellent", "helpful",
        "amazing", "perfect", "wonderful", "love", "appreciate",
    ]

    # Frustration-specific keywords
    FRUSTRATION_KEYWORDS = [
        "again", "already", "still", "not working", "doesn't work",
        "broken", "wrong", "failed", "error", "problem",
    ]

    def __init__(self) -> None:
        """Initialize the rule-based analyzer."""
        self._negative_pattern = self._compile_pattern(self.NEGATIVE_KEYWORDS)
        self._positive_pattern = self._compile_pattern(self.POSITIVE_KEYWORDS)
        self._frustration_pattern = self._compile_pattern(self.FRUSTRATION_KEYWORDS)

    def _compile_pattern(self, keywords: list[str]) -> re.Pattern:
        """Compile keywords into a regex pattern."""
        escaped = [re.escape(k) for k in keywords]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def extract_features(self, message: Message) -> SentimentFeatures:
        """Extract sentiment features from a message."""
        raise NotImplementedError("RuleBasedAnalyzer feature extraction pending")

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using rule-based approach."""
        raise NotImplementedError("RuleBasedAnalyzer analysis pending")
