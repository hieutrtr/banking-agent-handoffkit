"""Local LLM sentiment analyzer (Tier 2)."""

import time
from typing import Optional

try:
    import torch
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    pipeline = None  # type: ignore[assignment]
    TRANSFORMERS_AVAILABLE = False

from handoffkit.core.types import Message, SentimentResult
from handoffkit.utils.logging import get_logger

logger = get_logger("sentiment.local_llm")


class LocalLLMAnalyzer:
    """Local transformer-based sentiment analysis (Tier 2).

    Uses lightweight transformer models for semantic sentiment understanding:
    - DistilBERT: General-purpose sentiment (default, 268MB, ~92% accuracy)
    - FinBERT: Financial domain sentiment (438MB, ~94% for banking terms)

    Requires optional [ml] dependencies:
    - transformers>=4.36.0
    - torch>=2.1.0

    Target: <100ms evaluation time on CPU.

    Example:
        >>> from handoffkit.sentiment.local_llm import LocalLLMAnalyzer
        >>> from handoffkit.core.types import Message, MessageSpeaker
        >>> analyzer = LocalLLMAnalyzer()
        >>> msg = Message(speaker=MessageSpeaker.USER, content="This is great!")
        >>> result = await analyzer.analyze(msg)
        >>> result.score > 0.5  # Positive sentiment
        True
    """

    def __init__(
        self,
        device: str = "cpu",
        financial_domain: bool = False,
        threshold: float = 0.3,
    ) -> None:
        """Initialize local LLM analyzer.

        Args:
            device: Device to run on ("cpu" or "cuda" for GPU)
            financial_domain: If True, use FinBERT for financial text
            threshold: Sentiment threshold for escalation (default 0.3)

        Raises:
            ImportError: If transformers or torch not installed
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "Local LLM analyzer requires transformers and torch. "
                "Install with: pip install handoffkit[ml]"
            )

        self._threshold = threshold

        # Determine device for model execution
        # transformers uses: -1 for CPU, 0 for GPU 0
        if device == "cuda" and torch is not None and torch.cuda.is_available():
            self._device = 0
            logger.info("Using GPU (CUDA) for local LLM inference")
        else:
            self._device = -1
            logger.info("Using CPU for local LLM inference")

        # Select model based on domain
        if financial_domain:
            self._model_name = "ProsusAI/finbert"
            logger.info("Loading FinBERT model for financial domain")
        else:
            self._model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            logger.info("Loading DistilBERT model for general sentiment")

        # Initialize sentiment pipeline (downloads model on first run)
        logger.debug(f"Initializing sentiment pipeline with model: {self._model_name}")
        if pipeline is not None:
            self._sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self._model_name,
                device=self._device,
            )
            logger.debug("Sentiment pipeline initialized successfully")
        else:
            raise ImportError("transformers.pipeline not available")

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using local transformer model.

        Args:
            message: Current message to analyze
            history: Optional conversation history (unused in Tier 2)

        Returns:
            SentimentResult with score, frustration_level, and tier_used="local_llm"

        Example:
            >>> msg = Message(speaker="user", content="This is terrible!")
            >>> result = await analyzer.analyze(msg)
            >>> result.score < 0.3  # Negative sentiment
            True
            >>> result.tier_used
            'local_llm'
        """
        start_time = time.perf_counter()

        # Run model inference
        result = self._sentiment_pipeline(message.content)[0]

        # Map DistilBERT/FinBERT output to normalized 0.0-1.0 range
        # Model output: {"label": "POSITIVE"/"NEGATIVE", "score": 0.0-1.0}
        # - POSITIVE with score 0.95 means very positive → keep as 0.95
        # - NEGATIVE with score 0.85 means very negative → invert to 0.15
        if result["label"] == "POSITIVE":
            score = result["score"]  # Already 0.5-1.0 for positive
        else:  # NEGATIVE
            score = 1.0 - result["score"]  # Invert to 0.0-0.5

        # Calculate frustration level (inverse of sentiment score)
        frustration_level = 1.0 - score

        # Determine if escalation needed
        should_escalate = score < self._threshold

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        logger.debug(
            f"Local LLM analysis: score={score:.3f}, "
            f"frustration={frustration_level:.3f}, "
            f"label={result['label']}, "
            f"time={processing_time_ms:.2f}ms"
        )

        return SentimentResult(
            score=score,
            frustration_level=frustration_level,
            should_escalate=should_escalate,
            tier_used="local_llm",
            processing_time_ms=processing_time_ms,
        )

    def is_available(self) -> bool:
        """Check if ML dependencies are installed.

        Returns:
            True if transformers and torch are available, False otherwise
        """
        return TRANSFORMERS_AVAILABLE
