"""Cloud LLM sentiment analyzer (Tier 3).

This module provides cloud-based sentiment analysis using OpenAI or Anthropic APIs
for complex cases where local analysis is insufficient.

Requires optional [cloud] dependencies:
- openai>=1.0.0 for OpenAI provider
- anthropic>=0.25.0 for Anthropic provider

Example:
    >>> from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer
    >>> from handoffkit.core.types import Message, MessageSpeaker
    >>> analyzer = CloudLLMAnalyzer(provider="openai", api_key="sk-...")
    >>> await analyzer.initialize()
    >>> msg = Message(speaker=MessageSpeaker.USER, content="This is frustrating!")
    >>> result = await analyzer.analyze(msg)
    >>> result.score < 0.5  # Negative sentiment
    True
"""

import json
import time
from typing import Any, Optional

from handoffkit.core.types import Message, SentimentResult
from handoffkit.utils.logging import get_logger

# Conditional imports for OpenAI
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None  # type: ignore[assignment, misc]
    OPENAI_AVAILABLE = False

# Conditional imports for Anthropic
try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    AsyncAnthropic = None  # type: ignore[assignment, misc]
    ANTHROPIC_AVAILABLE = False

logger = get_logger("sentiment.cloud_llm")


class CloudLLMAnalyzer:
    """Cloud API-based sentiment analysis for complex cases (Tier 3).

    Uses cloud LLM APIs to analyze sentiment with highest accuracy.
    Only called for ambiguous cases (<10% of requests) to optimize costs.

    Supports:
    - OpenAI GPT models (default: gpt-4o-mini, $0.15/1M tokens)
    - Anthropic Claude models (default: claude-3-haiku-20240307)

    Target: <500ms evaluation time.

    Example:
        >>> from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer
        >>> from handoffkit.core.types import Message, MessageSpeaker
        >>> analyzer = CloudLLMAnalyzer(provider="openai", api_key="sk-...")
        >>> await analyzer.initialize()
        >>> msg = Message(speaker=MessageSpeaker.USER, content="This is frustrating!")
        >>> result = await analyzer.analyze(msg)
        >>> result.score < 0.5  # Negative sentiment
        True
    """

    SENTIMENT_PROMPT = """Analyze the sentiment of this customer service message.
Consider frustration level, urgency, and whether the user needs human assistance.

{history_context}

Current message: {message}

Respond with JSON only:
{{
  "sentiment_score": 0.0-1.0 (0=very negative, 1=very positive),
  "frustration_level": 0.0-1.0 (0=calm, 1=very frustrated),
  "should_escalate": true/false,
  "reasoning": "brief explanation"
}}"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 2.0,
    ) -> None:
        """Initialize cloud LLM analyzer.

        Args:
            provider: API provider ("openai" or "anthropic")
            api_key: API key for authentication
            model: Model to use (defaults to provider's cost-effective option)
            timeout: API timeout in seconds (default 2.0 for <500ms target with buffer)
        """
        self._provider = provider
        self._api_key = api_key
        self._model = model or self._default_model(provider)
        self._timeout = timeout
        self._client: Any = None
        self._initialized = False

    def _default_model(self, provider: str) -> str:
        """Get default model for provider.

        Returns cost-effective models by default:
        - OpenAI: gpt-4o-mini ($0.15/1M input tokens)
        - Anthropic: claude-3-haiku (fastest, cheapest Claude)
        """
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
        }
        return defaults.get(provider, "gpt-4o-mini")

    async def initialize(self) -> None:
        """Initialize the async API client.

        Creates the appropriate async client based on the provider.
        Safe to call multiple times (idempotent).
        """
        if self._provider == "openai" and OPENAI_AVAILABLE and AsyncOpenAI is not None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                timeout=self._timeout,
            )
            logger.info(f"OpenAI client initialized with model: {self._model}")
        elif (
            self._provider == "anthropic"
            and ANTHROPIC_AVAILABLE
            and AsyncAnthropic is not None
        ):
            # Anthropic uses httpx internally, timeout is in seconds
            self._client = AsyncAnthropic(
                api_key=self._api_key,
                timeout=self._timeout,
            )
            logger.info(f"Anthropic client initialized with model: {self._model}")
        else:
            logger.warning(
                f"Provider '{self._provider}' not available. "
                f"OpenAI available: {OPENAI_AVAILABLE}, "
                f"Anthropic available: {ANTHROPIC_AVAILABLE}"
            )

        self._initialized = True

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using cloud LLM API.

        Implements graceful fallback - never raises exceptions.
        Returns neutral result (0.5) on any error.

        Args:
            message: Current message to analyze
            history: Conversation history for context

        Returns:
            SentimentResult with score, frustration_level, and tier_used="cloud_llm"
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.perf_counter()

        try:
            if self._provider == "openai":
                result = await self._analyze_openai(message.content, history)
            elif self._provider == "anthropic":
                result = await self._analyze_anthropic(message.content, history)
            else:
                logger.warning(f"Unknown provider: {self._provider}")
                return self._create_neutral_result(start_time)

            processing_time_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"Cloud LLM analysis: score={result.get('sentiment_score', 0.5):.3f}, "
                f"frustration={result.get('frustration_level', 0.5):.3f}, "
                f"time={processing_time_ms:.2f}ms"
            )

            return SentimentResult(
                score=result.get("sentiment_score", 0.5),
                frustration_level=result.get("frustration_level", 0.5),
                should_escalate=result.get("should_escalate", False),
                tier_used="cloud_llm",
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            # Graceful fallback - log error but don't raise
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                f"Cloud LLM error ({type(e).__name__}): {e}. "
                f"Returning neutral result. Time: {processing_time_ms:.2f}ms"
            )
            return self._create_neutral_result(start_time)

    async def _analyze_openai(
        self, content: str, history: Optional[list[Message]] = None
    ) -> dict[str, Any]:
        """Analyze sentiment using OpenAI API.

        Args:
            content: Message content to analyze
            history: Conversation history for context

        Returns:
            Parsed JSON response with sentiment fields
        """
        if self._client is None:
            raise RuntimeError("OpenAI client not initialized")

        # Build history context
        history_context = self._build_history_context(history)

        # Build prompt
        prompt = self.SENTIMENT_PROMPT.format(
            history_context=history_context, message=content
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analysis expert. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0.0,  # Deterministic responses
        )

        response_text = response.choices[0].message.content
        return self._parse_response(response_text)

    async def _analyze_anthropic(
        self, content: str, history: Optional[list[Message]] = None
    ) -> dict[str, Any]:
        """Analyze sentiment using Anthropic API.

        Args:
            content: Message content to analyze
            history: Conversation history for context

        Returns:
            Parsed JSON response with sentiment fields
        """
        if self._client is None:
            raise RuntimeError("Anthropic client not initialized")

        # Build history context
        history_context = self._build_history_context(history)

        # Build prompt
        prompt = self.SENTIMENT_PROMPT.format(
            history_context=history_context, message=content
        )

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
            system="You are a sentiment analysis expert. Always respond with valid JSON only, no explanation.",
        )

        response_text = response.content[0].text
        return self._parse_response(response_text)

    def _build_history_context(
        self, history: Optional[list[Message]] = None
    ) -> str:
        """Build context string from conversation history.

        Args:
            history: Conversation history

        Returns:
            Formatted history context string
        """
        if not history:
            return "No previous conversation history."

        # Take last 5 messages for context
        recent_history = history[-5:]
        context_lines = ["Previous conversation:"]

        for msg in recent_history:
            speaker = "User" if msg.speaker.value == "user" else "AI"
            # Truncate long messages
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            context_lines.append(f"{speaker}: {content}")

        return "\n".join(context_lines)

    def _parse_response(self, response_text: Optional[str]) -> dict[str, Any]:
        """Parse JSON response from LLM.

        Args:
            response_text: Raw response text from API

        Returns:
            Parsed dictionary with sentiment fields

        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        if not response_text:
            raise ValueError("Empty response from API")

        try:
            result = json.loads(response_text)

            # Validate and normalize fields
            return {
                "sentiment_score": self._clamp(
                    float(result.get("sentiment_score", 0.5)), 0.0, 1.0
                ),
                "frustration_level": self._clamp(
                    float(result.get("frustration_level", 0.5)), 0.0, 1.0
                ),
                "should_escalate": bool(result.get("should_escalate", False)),
                "reasoning": str(result.get("reasoning", "")),
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))

    def _create_neutral_result(self, start_time: float) -> SentimentResult:
        """Create neutral result for error fallback.

        Args:
            start_time: When processing started (for timing)

        Returns:
            Neutral SentimentResult (score=0.5)
        """
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        return SentimentResult(
            score=0.5,
            frustration_level=0.5,
            should_escalate=False,
            tier_used="cloud_llm",
            processing_time_ms=processing_time_ms,
        )

    def is_available(self) -> bool:
        """Check if API credentials are configured.

        Returns:
            True if API key is set, False otherwise
        """
        return self._api_key is not None
