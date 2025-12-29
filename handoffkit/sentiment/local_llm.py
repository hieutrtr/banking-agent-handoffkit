"""Local LLM sentiment analyzer (Tier 2)."""

from typing import Optional

from handoffkit.core.types import Message, SentimentResult


class LocalLLMAnalyzer:
    """Local transformer-based sentiment analysis.

    Uses lightweight models like:
    - distilbert-base-uncased-finetuned-sst-2-english
    - cardiffnlp/twitter-roberta-base-sentiment

    Requires optional [ml] dependencies:
    - transformers>=4.36.0
    - torch>=2.1.0

    Target: <100ms evaluation time.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        device: Optional[str] = None,
    ) -> None:
        """Initialize local LLM analyzer.

        Args:
            model_name: HuggingFace model identifier.
            device: Device to run on (cpu/cuda/mps).
        """
        self._model_name = model_name
        self._device = device
        self._model = None
        self._tokenizer = None
        self._initialized = False

    async def initialize(self) -> None:
        """Load the model and tokenizer.

        Raises:
            ImportError: If ML dependencies are not installed.
        """
        raise NotImplementedError("LocalLLMAnalyzer initialization pending")

    async def analyze(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
    ) -> SentimentResult:
        """Analyze sentiment using local transformer model."""
        raise NotImplementedError("LocalLLMAnalyzer analysis pending")

    def is_available(self) -> bool:
        """Check if ML dependencies are installed."""
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
            return True
        except ImportError:
            return False
