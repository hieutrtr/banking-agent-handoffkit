"""Sentiment analysis module for handoff detection."""

from typing import Any, Optional

from handoffkit.core.config import SentimentConfig
from handoffkit.core.types import Message, SentimentResult
from handoffkit.sentiment.models import SentimentTier
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer
from handoffkit.sentiment.local_llm import LocalLLMAnalyzer
from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer


class SentimentAnalyzer:
    """Main sentiment analyzer with 3-tier fallback architecture.

    Tiers:
    1. Rule-based: Fast keyword scoring (<10ms)
    2. Local LLM: Lightweight transformer model (<100ms)
    3. Cloud LLM: Full API call for complex cases (<500ms)
    """

    def __init__(self, config: Optional[SentimentConfig] = None) -> None:
        """Initialize analyzer with configuration."""
        self._config = config or SentimentConfig()
        self._rule_based = RuleBasedAnalyzer()
        self._local_llm: Optional[LocalLLMAnalyzer] = None
        self._cloud_llm: Optional[CloudLLMAnalyzer] = None

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment with automatic tier selection.

        Args:
            message: Current message to analyze.
            history: Conversation history for context.

        Returns:
            SentimentResult with score and escalation recommendation.
        """
        raise NotImplementedError("SentimentAnalyzer implementation pending")

    async def analyze_with_tier(
        self,
        message: Message,
        tier: SentimentTier,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using a specific tier.

        Args:
            message: Message to analyze.
            tier: Which tier to use.
            history: Conversation history.

        Returns:
            SentimentResult from the specified tier.
        """
        raise NotImplementedError("SentimentAnalyzer tier selection pending")
