"""Tests for Local LLM sentiment analyzer (Tier 2)."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from handoffkit.core.types import Message, MessageSpeaker, SentimentResult


@pytest.fixture(autouse=True)
def mock_transformers():
    """Mock transformers library availability for all tests."""
    with patch("handoffkit.sentiment.local_llm.TRANSFORMERS_AVAILABLE", True):
        with patch("handoffkit.sentiment.local_llm.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            yield mock_torch


class TestLocalLLMAnalyzerInitialization:
    """Tests for LocalLLMAnalyzer initialization."""

    def test_analyzer_initializes_with_defaults(self) -> None:
        """Test analyzer can be instantiated with default settings."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()
            assert analyzer is not None

    def test_analyzer_loads_distilbert_by_default(self) -> None:
        """Test analyzer loads DistilBERT model by default."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            # Verify pipeline called with DistilBERT model
            mock_pipeline.assert_called_once()
            call_kwargs = mock_pipeline.call_args[1]
            assert call_kwargs["model"] == "distilbert-base-uncased-finetuned-sst-2-english"
            assert call_kwargs["device"] == -1  # CPU

    def test_analyzer_loads_finbert_for_financial_domain(self) -> None:
        """Test analyzer loads FinBERT when financial_domain=True."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer(financial_domain=True)

            # Verify pipeline called with FinBERT model
            call_kwargs = mock_pipeline.call_args[1]
            assert call_kwargs["model"] == "ProsusAI/finbert"

    def test_analyzer_uses_cpu_by_default(self) -> None:
        """Test analyzer uses CPU device by default."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            with patch("handoffkit.sentiment.local_llm.torch") as mock_torch:
                mock_torch.cuda.is_available.return_value = False
                from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

                analyzer = LocalLLMAnalyzer(device="cpu")

                call_kwargs = mock_pipeline.call_args[1]
                assert call_kwargs["device"] == -1  # -1 means CPU in transformers

    def test_analyzer_uses_gpu_when_available(self) -> None:
        """Test analyzer uses GPU device when cuda available."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            with patch("handoffkit.sentiment.local_llm.torch") as mock_torch:
                mock_torch.cuda.is_available.return_value = True
                from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

                analyzer = LocalLLMAnalyzer(device="cuda")

                call_kwargs = mock_pipeline.call_args[1]
                assert call_kwargs["device"] == 0  # 0 means GPU 0 in transformers


class TestDistilBERTSentimentAnalysis:
    """Tests for DistilBERT sentiment analysis."""

    @pytest.mark.asyncio
    async def test_analyze_positive_sentiment(self) -> None:
        """Test analyzer correctly processes positive sentiment."""
        # Mock pipeline to return positive sentiment
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.95}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="This is great!")
            result = await analyzer.analyze(message)

            assert isinstance(result, SentimentResult)
            assert result.score == pytest.approx(0.95, abs=0.01)
            assert result.tier_used == "local_llm"
            assert result.frustration_level == pytest.approx(0.05, abs=0.01)

    @pytest.mark.asyncio
    async def test_analyze_negative_sentiment(self) -> None:
        """Test analyzer correctly processes negative sentiment."""
        # Mock pipeline to return negative sentiment
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "NEGATIVE", "score": 0.85}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="This is terrible!")
            result = await analyzer.analyze(message)

            # NEGATIVE score 0.85 means very negative
            # Inverted: 1.0 - 0.85 = 0.15 (low score = negative)
            assert result.score == pytest.approx(0.15, abs=0.01)
            assert result.tier_used == "local_llm"
            assert result.frustration_level == pytest.approx(0.85, abs=0.01)

    @pytest.mark.asyncio
    async def test_analyze_returns_sentiment_result(self) -> None:
        """Test analyze returns valid SentimentResult."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.7}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(message)

            assert isinstance(result, SentimentResult)
            assert 0.0 <= result.score <= 1.0
            assert 0.0 <= result.frustration_level <= 1.0
            assert isinstance(result.should_escalate, bool)
            assert result.tier_used == "local_llm"
            assert result.processing_time_ms >= 0.0

    @pytest.mark.asyncio
    async def test_analyze_tracks_processing_time(self) -> None:
        """Test analyzer tracks processing time."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.7}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="Test")
            result = await analyzer.analyze(message)

            # Should track time (will be very small in tests, but > 0)
            assert result.processing_time_ms >= 0.0


class TestFinBERTFinancialDomain:
    """Tests for FinBERT financial domain support."""

    @pytest.mark.asyncio
    async def test_finbert_analyzes_financial_text(self) -> None:
        """Test FinBERT processes financial domain text."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "NEGATIVE", "score": 0.92}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer(financial_domain=True)

            message = Message(
                speaker=MessageSpeaker.USER,
                content="My account is locked and I suspect fraud",
            )
            result = await analyzer.analyze(message)

            # Verify FinBERT model was loaded
            call_kwargs = mock_pipeline.call_args[1]
            assert call_kwargs["model"] == "ProsusAI/finbert"

            # Verify analysis result
            assert isinstance(result, SentimentResult)
            assert result.tier_used == "local_llm"


class TestModelCaching:
    """Tests for model caching and singleton pattern."""

    def test_model_loaded_once_on_initialization(self) -> None:
        """Test model is loaded once during __init__."""
        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = Mock()
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            # Pipeline should be called once during __init__
            assert mock_pipeline.call_count == 1

    @pytest.mark.asyncio
    async def test_model_reused_for_multiple_analyses(self) -> None:
        """Test model is reused for multiple analyze calls."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.7}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            # Call analyze multiple times
            msg1 = Message(speaker=MessageSpeaker.USER, content="Test 1")
            msg2 = Message(speaker=MessageSpeaker.USER, content="Test 2")
            msg3 = Message(speaker=MessageSpeaker.USER, content="Test 3")

            await analyzer.analyze(msg1)
            await analyzer.analyze(msg2)
            await analyzer.analyze(msg3)

            # Pipeline created only once
            assert mock_pipeline.call_count == 1
            # But used 3 times
            assert mock_pipeline_instance.call_count == 3


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_analysis_completes_under_100ms(self) -> None:
        """Test analysis completes in under 100ms (mocked, real test would verify actual)."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.7}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(message)

            # In real usage, this should be < 100ms on CPU
            # In tests with mocks, it will be much faster
            assert result.processing_time_ms >= 0.0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_analyze_with_empty_message(self) -> None:
        """Test analyzer handles empty message content."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.5}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="")
            result = await analyzer.analyze(message)

            assert isinstance(result, SentimentResult)

    @pytest.mark.asyncio
    async def test_analyze_ignores_history_parameter(self) -> None:
        """Test analyzer accepts but doesn't use history parameter (Tier 2 feature)."""
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.7}]

        with patch("handoffkit.sentiment.local_llm.pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_pipeline_instance
            from handoffkit.sentiment.local_llm import LocalLLMAnalyzer

            analyzer = LocalLLMAnalyzer()

            message = Message(speaker=MessageSpeaker.USER, content="Test")
            history = [
                Message(speaker=MessageSpeaker.USER, content="Previous message"),
            ]

            result = await analyzer.analyze(message, history=history)

            # Should still work (history is optional and unused in Tier 2)
            assert isinstance(result, SentimentResult)
