"""Sentiment analysis module for handoff detection."""

from typing import Any, Optional

from handoffkit.core.config import SentimentConfig
from handoffkit.core.types import Message, SentimentResult
from handoffkit.sentiment.models import SentimentTier
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer
from handoffkit.sentiment.local_llm import LocalLLMAnalyzer, TRANSFORMERS_AVAILABLE
from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer
from handoffkit.utils.logging import get_logger

logger = get_logger("sentiment.analyzer")


class SentimentAnalyzer:
    """Main sentiment analyzer with 3-tier fallback architecture.

    Tiers:
    1. Rule-based: Fast keyword scoring (<10ms)
    2. Local LLM: Lightweight transformer model (<100ms)
    3. Cloud LLM: Full API call for complex cases (<500ms)

    Example:
        >>> from handoffkit.sentiment.analyzer import SentimentAnalyzer
        >>> from handoffkit.core.types import Message
        >>> analyzer = SentimentAnalyzer()
        >>> msg = Message(speaker="user", content="This is frustrating")
        >>> result = await analyzer.analyze(msg)
        >>> result.score < 0.5  # Negative sentiment
        True
    """

    def __init__(self, config: Optional[SentimentConfig] = None) -> None:
        """Initialize analyzer with configuration.

        Args:
            config: Sentiment analysis configuration
        """
        self._config = config or SentimentConfig()
        self._rule_based = RuleBasedAnalyzer(threshold=self._config.sentiment_threshold)
        self._local_llm: Optional[LocalLLMAnalyzer] = None
        self._cloud_llm: Optional[CloudLLMAnalyzer] = None

        # Initialize Local LLM (Tier 2) if enabled and available
        if self._config.enable_local_llm and TRANSFORMERS_AVAILABLE:
            try:
                self._local_llm = LocalLLMAnalyzer(
                    financial_domain=self._config.financial_domain,
                    threshold=self._config.sentiment_threshold,
                )
                logger.info("Local LLM (Tier 2) initialized successfully")
            except ImportError as e:
                logger.warning(
                    f"Local LLM requested but not available: {e}. "
                    "Falling back to Tier 1 only."
                )

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment with automatic tier selection.

        The analyzer implements a 3-tier escalation strategy:
        - Tier 1 (Rule-based): Always runs first, <10ms
        - Tier 2 (Local LLM): Escalates if Tier 1 result is ambiguous
        - Tier 3 (Cloud LLM): Optional, for complex cases

        Escalation criteria:
        - Tier 1 → Tier 2: Score within 0.1 of threshold (ambiguous)
        - Tier 2 → Tier 3: Not implemented yet

        Args:
            message: Current message to analyze
            history: Conversation history for context

        Returns:
            SentimentResult with score and escalation recommendation

        Example:
            >>> msg = Message(speaker="user", content="I guess this is okay")
            >>> result = await analyzer.analyze(msg)
            >>> result.tier_used  # May be "rule_based" or "local_llm" depending on ambiguity
            'rule_based'
        """
        # Tier 1: Always run rule-based first (fastest)
        tier1_result = await self._rule_based.analyze(message, history)

        # Check if we should escalate to Tier 2
        if self._config.enable_local_llm and self._local_llm is not None:
            # Escalate if Tier 1 is ambiguous (score near threshold)
            ambiguity_range = 0.1
            if abs(tier1_result.score - self._config.sentiment_threshold) < ambiguity_range:
                logger.debug(
                    f"Escalating to Tier 2: Tier 1 score {tier1_result.score:.3f} "
                    f"is within {ambiguity_range} of threshold "
                    f"{self._config.sentiment_threshold}"
                )
                # Use Tier 2 for more accurate analysis
                tier2_result = await self._local_llm.analyze(message, history)
                logger.debug(
                    f"Tier 2 result: score={tier2_result.score:.3f}, "
                    f"processing_time={tier2_result.processing_time_ms:.2f}ms"
                )
                return tier2_result

        # Return Tier 1 result if no escalation needed
        logger.debug(
            f"Using Tier 1 result: score={tier1_result.score:.3f}, "
            f"processing_time={tier1_result.processing_time_ms:.2f}ms"
        )
        return tier1_result

    async def analyze_with_tier(
        self,
        message: Message,
        tier: SentimentTier,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using a specific tier.

        Args:
            message: Message to analyze
            tier: Which tier to use (RULE_BASED, LOCAL_LLM, or CLOUD_LLM)
            history: Conversation history

        Returns:
            SentimentResult from the specified tier

        Raises:
            ValueError: If requested tier is not available

        Example:
            >>> from handoffkit.sentiment.models import SentimentTier
            >>> result = await analyzer.analyze_with_tier(msg, SentimentTier.LOCAL_LLM)
            >>> result.tier_used
            'local_llm'
        """
        if tier == SentimentTier.RULE_BASED:
            return await self._rule_based.analyze(message, history)

        elif tier == SentimentTier.LOCAL_LLM:
            if self._local_llm is None:
                raise ValueError(
                    "Local LLM tier not available. "
                    "Install with: pip install handoffkit[ml]"
                )
            return await self._local_llm.analyze(message, history)

        elif tier == SentimentTier.CLOUD_LLM:
            if self._cloud_llm is None:
                raise ValueError(
                    "Cloud LLM tier not available. "
                    "Configure with cloud_llm_enabled=True and provide API keys."
                )
            return await self._cloud_llm.analyze(message, history)

        else:
            raise ValueError(f"Unknown sentiment tier: {tier}")
