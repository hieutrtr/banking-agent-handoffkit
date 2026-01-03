"""Sentiment analysis module for handoff detection."""

from typing import Optional

from handoffkit.core.config import SentimentConfig
from handoffkit.core.types import Message, SentimentResult
from handoffkit.sentiment.cloud_llm import (
    CloudLLMAnalyzer,
    OPENAI_AVAILABLE,
    ANTHROPIC_AVAILABLE,
)
from handoffkit.sentiment.local_llm import LocalLLMAnalyzer, TRANSFORMERS_AVAILABLE
from handoffkit.sentiment.models import SentimentTier
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer
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

        # Initialize Cloud LLM (Tier 3) if enabled and configured
        if self._config.enable_cloud_llm and self._config.cloud_llm_api_key:
            cloud_available = (
                (self._config.cloud_llm_provider == "openai" and OPENAI_AVAILABLE)
                or (
                    self._config.cloud_llm_provider == "anthropic"
                    and ANTHROPIC_AVAILABLE
                )
            )
            if cloud_available or self._config.cloud_llm_provider:
                self._cloud_llm = CloudLLMAnalyzer(
                    provider=self._config.cloud_llm_provider or "openai",
                    api_key=self._config.cloud_llm_api_key,
                    model=self._config.cloud_llm_model,
                )
                logger.info(
                    f"Cloud LLM (Tier 3) initialized with provider: "
                    f"{self._config.cloud_llm_provider or 'openai'}"
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
        - Tier 3 (Cloud LLM): Escalates if Tier 2 score is below threshold

        Escalation criteria:
        - Tier 1 → Tier 2: Score within 0.1 of threshold (ambiguous)
        - Tier 2 → Tier 3: Score below cloud_llm_threshold (default 0.3)

        Args:
            message: Current message to analyze
            history: Conversation history for context

        Returns:
            SentimentResult with score and escalation recommendation

        Example:
            >>> msg = Message(speaker="user", content="I guess this is okay")
            >>> result = await analyzer.analyze(msg)
            >>> result.tier_used  # May be "rule_based", "local_llm", or "cloud_llm"
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

                # Check if we should escalate to Tier 3
                if self._config.enable_cloud_llm and self._cloud_llm is not None:
                    if tier2_result.score < self._config.cloud_llm_threshold:
                        logger.debug(
                            f"Escalating to Tier 3: Tier 2 score {tier2_result.score:.3f} "
                            f"below threshold {self._config.cloud_llm_threshold}"
                        )
                        try:
                            tier3_result = await self._cloud_llm.analyze(message, history)
                            # Check if cloud LLM returned a valid result (not fallback neutral)
                            # CloudLLMAnalyzer returns neutral 0.5 on error - use tier2 instead
                            if tier3_result.score == 0.5 and tier3_result.frustration_level == 0.5:
                                logger.debug(
                                    "Tier 3 returned neutral result (possible error), "
                                    "using Tier 2 result instead"
                                )
                                return tier2_result
                            logger.debug(
                                f"Tier 3 result: score={tier3_result.score:.3f}, "
                                f"processing_time={tier3_result.processing_time_ms:.2f}ms"
                            )
                            return tier3_result
                        except Exception as e:
                            # Graceful fallback to Tier 2 on any cloud error (AC #3)
                            logger.warning(
                                f"Tier 3 error ({type(e).__name__}): {e}. "
                                "Falling back to Tier 2 result."
                            )
                            return tier2_result

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
