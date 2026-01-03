"""Tests for CloudLLMAnalyzer (Tier 3)."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from handoffkit.core.config import SentimentConfig
from handoffkit.core.types import Message, MessageSpeaker, SentimentResult
from handoffkit.sentiment.analyzer import SentimentAnalyzer
from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer


class TestCloudLLMAnalyzerInit:
    """Tests for CloudLLMAnalyzer initialization."""

    def test_init_default_provider(self) -> None:
        """Test default provider is openai."""
        analyzer = CloudLLMAnalyzer(api_key="test-key")
        assert analyzer._provider == "openai"

    def test_init_openai_default_model(self) -> None:
        """Test OpenAI default model is gpt-4o-mini."""
        analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
        assert analyzer._model == "gpt-4o-mini"

    def test_init_anthropic_default_model(self) -> None:
        """Test Anthropic default model is claude-3-haiku."""
        analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
        assert analyzer._model == "claude-3-haiku-20240307"

    def test_init_custom_model(self) -> None:
        """Test custom model is used."""
        analyzer = CloudLLMAnalyzer(
            provider="openai", api_key="test-key", model="gpt-4o"
        )
        assert analyzer._model == "gpt-4o"

    def test_is_available_with_api_key(self) -> None:
        """Test is_available returns True when API key is set."""
        analyzer = CloudLLMAnalyzer(api_key="test-key")
        assert analyzer.is_available() is True

    def test_is_available_without_api_key(self) -> None:
        """Test is_available returns False when API key is not set."""
        analyzer = CloudLLMAnalyzer()
        assert analyzer.is_available() is False


class TestCloudLLMAnalyzerOpenAI:
    """Tests for OpenAI integration."""

    @pytest.mark.asyncio
    async def test_initialize_openai_client(self) -> None:
        """Test OpenAI client initialization."""
        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch("handoffkit.sentiment.cloud_llm.AsyncOpenAI") as mock_openai:
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            mock_openai.assert_called_once_with(
                api_key="test-key", timeout=2.0
            )
            assert analyzer._initialized is True

    @pytest.mark.asyncio
    async def test_analyze_openai_positive_sentiment(self) -> None:
        """Test OpenAI analysis returns positive sentiment."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.85, "frustration_level": 0.1, "should_escalate": false, "reasoning": "Customer is satisfied"}'
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Thank you so much!")
            result = await analyzer.analyze(msg)

            assert result.score == 0.85
            assert result.frustration_level == 0.1
            assert result.should_escalate is False
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_analyze_openai_negative_sentiment(self) -> None:
        """Test OpenAI analysis returns negative sentiment."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.15, "frustration_level": 0.9, "should_escalate": true, "reasoning": "Customer is very frustrated"}'
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="This is terrible!")
            result = await analyzer.analyze(msg)

            assert result.score == 0.15
            assert result.frustration_level == 0.9
            assert result.should_escalate is True
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_analyze_openai_with_history(self) -> None:
        """Test OpenAI analysis includes conversation history."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.5, "frustration_level": 0.5, "should_escalate": false, "reasoning": "Neutral"}'
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            history = [
                Message(speaker=MessageSpeaker.USER, content="I need help"),
                Message(speaker=MessageSpeaker.AI, content="How can I assist?"),
            ]
            msg = Message(speaker=MessageSpeaker.USER, content="My order is late")
            result = await analyzer.analyze(msg, history)

            # Verify the API was called with history included
            call_args = mock_client.chat.completions.create.call_args
            assert "messages" in call_args.kwargs
            # Should include system message + conversation context
            assert len(call_args.kwargs["messages"]) >= 1


class TestCloudLLMAnalyzerAnthropic:
    """Tests for Anthropic integration."""

    @pytest.mark.asyncio
    async def test_initialize_anthropic_client(self) -> None:
        """Test Anthropic client initialization."""
        with patch(
            "handoffkit.sentiment.cloud_llm.ANTHROPIC_AVAILABLE", True
        ), patch("handoffkit.sentiment.cloud_llm.AsyncAnthropic") as mock_anthropic:
            analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
            await analyzer.initialize()

            mock_anthropic.assert_called_once_with(
                api_key="test-key", timeout=2.0
            )
            assert analyzer._initialized is True

    @pytest.mark.asyncio
    async def test_analyze_anthropic_positive_sentiment(self) -> None:
        """Test Anthropic analysis returns positive sentiment."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"sentiment_score": 0.9, "frustration_level": 0.05, "should_escalate": false, "reasoning": "Very happy customer"}'
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.ANTHROPIC_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncAnthropic", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="This is amazing!")
            result = await analyzer.analyze(msg)

            assert result.score == 0.9
            assert result.frustration_level == 0.05
            assert result.should_escalate is False
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_analyze_anthropic_negative_sentiment(self) -> None:
        """Test Anthropic analysis returns negative sentiment."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"sentiment_score": 0.1, "frustration_level": 0.95, "should_escalate": true, "reasoning": "Extremely frustrated customer"}'
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.ANTHROPIC_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncAnthropic", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="I hate this service!")
            result = await analyzer.analyze(msg)

            assert result.score == 0.1
            assert result.frustration_level == 0.95
            assert result.should_escalate is True
            assert result.tier_used == "cloud_llm"


class TestCloudLLMAnalyzerErrorHandling:
    """Tests for error handling and graceful fallback."""

    @pytest.mark.asyncio
    async def test_fallback_on_api_error(self) -> None:
        """Test graceful fallback when API call fails."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on error
            assert result.score == 0.5
            assert result.frustration_level == 0.5
            assert result.should_escalate is False
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_fallback_on_timeout(self) -> None:
        """Test graceful fallback when API times out."""
        import asyncio

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on timeout
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json_response(self) -> None:
        """Test graceful fallback when API returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not valid JSON"))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on parse error
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_fallback_on_missing_json_fields(self) -> None:
        """Test graceful fallback when JSON response is missing required fields."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.5}'  # Missing other fields
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should use defaults for missing fields
            assert result.score == 0.5
            assert result.frustration_level == 0.5
            assert result.should_escalate is False

    @pytest.mark.asyncio
    async def test_unknown_provider_raises_error(self) -> None:
        """Test that unknown provider raises ValueError."""
        analyzer = CloudLLMAnalyzer(provider="unknown", api_key="test-key")
        await analyzer.initialize()

        msg = Message(speaker=MessageSpeaker.USER, content="Test message")
        result = await analyzer.analyze(msg)

        # Should return neutral result for unknown provider
        assert result.score == 0.5
        assert result.tier_used == "cloud_llm"


class TestCloudLLMAnalyzerPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_processing_time_tracked(self) -> None:
        """Test that processing time is tracked."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.5, "frustration_level": 0.5, "should_escalate": false, "reasoning": "Neutral"}'
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Processing time should be tracked
            assert result.processing_time_ms >= 0


class TestCloudLLMAnalyzerConditionalImports:
    """Tests for conditional imports when dependencies not installed."""

    def test_openai_not_available_flag(self) -> None:
        """Test OPENAI_AVAILABLE flag when openai not installed."""
        with patch.dict("sys.modules", {"openai": None}):
            # This tests that the module handles missing openai gracefully
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            # Should still be able to create instance
            assert analyzer._provider == "openai"

    def test_anthropic_not_available_flag(self) -> None:
        """Test ANTHROPIC_AVAILABLE flag when anthropic not installed."""
        with patch.dict("sys.modules", {"anthropic": None}):
            # This tests that the module handles missing anthropic gracefully
            analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
            # Should still be able to create instance
            assert analyzer._provider == "anthropic"

    @pytest.mark.asyncio
    async def test_initialize_without_openai_installed(self) -> None:
        """Test initialization when openai package not installed."""
        with patch("handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", False):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            # Client should be None when package not available
            assert analyzer._client is None
            assert analyzer._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_anthropic_installed(self) -> None:
        """Test initialization when anthropic package not installed."""
        with patch("handoffkit.sentiment.cloud_llm.ANTHROPIC_AVAILABLE", False):
            analyzer = CloudLLMAnalyzer(provider="anthropic", api_key="test-key")
            await analyzer.initialize()

            # Client should be None when package not available
            assert analyzer._client is None
            assert analyzer._initialized is True


class TestCloudLLMAnalyzerAutoInitialize:
    """Tests for auto-initialization behavior."""

    @pytest.mark.asyncio
    async def test_auto_initialize_on_analyze(self) -> None:
        """Test that analyze() auto-initializes if not initialized."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.5, "frustration_level": 0.5, "should_escalate": false, "reasoning": "Neutral"}'
                )
            )
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            assert analyzer._initialized is False

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            await analyzer.analyze(msg)

            assert analyzer._initialized is True


class TestSentimentConfigCloudLLM:
    """Tests for SentimentConfig cloud LLM fields."""

    def test_default_cloud_llm_disabled(self) -> None:
        """Test cloud LLM is disabled by default."""
        config = SentimentConfig()
        assert config.enable_cloud_llm is False
        assert config.cloud_llm_provider is None
        assert config.cloud_llm_api_key is None

    def test_cloud_llm_config_fields(self) -> None:
        """Test cloud LLM configuration fields."""
        config = SentimentConfig(
            enable_cloud_llm=True,
            cloud_llm_provider="openai",
            cloud_llm_api_key="test-key",
            cloud_llm_model="gpt-4o",
            cloud_llm_threshold=0.25,
        )
        assert config.enable_cloud_llm is True
        assert config.cloud_llm_provider == "openai"
        assert config.cloud_llm_api_key == "test-key"
        assert config.cloud_llm_model == "gpt-4o"
        assert config.cloud_llm_threshold == 0.25

    def test_cloud_llm_default_model(self) -> None:
        """Test default cloud LLM model is gpt-4o-mini."""
        config = SentimentConfig()
        assert config.cloud_llm_model == "gpt-4o-mini"

    def test_cloud_llm_default_threshold(self) -> None:
        """Test default cloud LLM threshold is 0.3."""
        config = SentimentConfig()
        assert config.cloud_llm_threshold == 0.3

    def test_cloud_llm_anthropic_provider(self) -> None:
        """Test Anthropic as cloud LLM provider."""
        config = SentimentConfig(
            enable_cloud_llm=True,
            cloud_llm_provider="anthropic",
            cloud_llm_api_key="test-anthropic-key",
        )
        assert config.cloud_llm_provider == "anthropic"


class TestSentimentAnalyzerCloudLLMIntegration:
    """Tests for SentimentAnalyzer cloud LLM integration."""

    def test_cloud_llm_not_initialized_when_disabled(self) -> None:
        """Test cloud LLM is not initialized when enable_cloud_llm=False."""
        config = SentimentConfig(enable_cloud_llm=False)
        analyzer = SentimentAnalyzer(config=config)
        assert analyzer._cloud_llm is None

    def test_cloud_llm_not_initialized_without_api_key(self) -> None:
        """Test cloud LLM is not initialized without API key."""
        config = SentimentConfig(
            enable_cloud_llm=True, cloud_llm_provider="openai"
        )
        analyzer = SentimentAnalyzer(config=config)
        assert analyzer._cloud_llm is None

    def test_cloud_llm_initialized_with_config(self) -> None:
        """Test cloud LLM is initialized with valid configuration."""
        with patch(
            "handoffkit.sentiment.analyzer.OPENAI_AVAILABLE", True
        ):
            config = SentimentConfig(
                enable_cloud_llm=True,
                cloud_llm_provider="openai",
                cloud_llm_api_key="test-key",
            )
            analyzer = SentimentAnalyzer(config=config)
            assert analyzer._cloud_llm is not None
            assert analyzer._cloud_llm._provider == "openai"
            assert analyzer._cloud_llm._api_key == "test-key"


class TestTier2ToTier3Escalation:
    """Tests for Tier 2 to Tier 3 escalation flow (HIGH #3 fix)."""

    @pytest.mark.asyncio
    async def test_tier2_to_tier3_escalation_full_flow(self) -> None:
        """Test full escalation flow from Tier 2 to Tier 3 when score is below threshold.

        This test validates the complete Tier 2 → Tier 3 escalation:
        1. Tier 1 returns ambiguous result (within 0.1 of threshold)
        2. Tier 2 returns low confidence score (below cloud_llm_threshold)
        3. Tier 3 is called and returns final result
        """
        # Setup mock cloud LLM response
        mock_cloud_response = MagicMock()
        mock_cloud_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.15, "frustration_level": 0.85, "should_escalate": true, "reasoning": "Cloud LLM analysis"}'
                )
            )
        ]
        mock_cloud_client = AsyncMock()
        mock_cloud_client.chat.completions.create = AsyncMock(return_value=mock_cloud_response)

        with patch("handoffkit.sentiment.analyzer.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.analyzer.TRANSFORMERS_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_cloud_client), \
             patch("handoffkit.sentiment.local_llm.TRANSFORMERS_AVAILABLE", True):

            config = SentimentConfig(
                enable_local_llm=True,
                enable_cloud_llm=True,
                cloud_llm_provider="openai",
                cloud_llm_api_key="test-key",
                cloud_llm_threshold=0.3,  # Escalate when Tier 2 < 0.3
                sentiment_threshold=0.5,
            )
            analyzer = SentimentAnalyzer(config=config)

            # Mock local LLM to return low score (triggers Tier 3 escalation)
            mock_local_llm = AsyncMock()
            mock_local_llm.analyze = AsyncMock(
                return_value=SentimentResult(
                    score=0.25,  # Below cloud_llm_threshold of 0.3
                    frustration_level=0.7,
                    should_escalate=True,
                    tier_used="local_llm",
                    processing_time_ms=50.0,
                )
            )
            analyzer._local_llm = mock_local_llm

            # Mock rule-based to return ambiguous score (triggers Tier 2)
            mock_rule_based = AsyncMock()
            mock_rule_based.analyze = AsyncMock(
                return_value=SentimentResult(
                    score=0.45,  # Within 0.1 of threshold 0.5
                    frustration_level=0.5,
                    should_escalate=False,
                    tier_used="rule_based",
                    processing_time_ms=5.0,
                )
            )
            analyzer._rule_based = mock_rule_based

            msg = Message(speaker=MessageSpeaker.USER, content="This is frustrating!")
            result = await analyzer.analyze(msg)

            # Should return Tier 3 result
            assert result.tier_used == "cloud_llm"
            assert result.score == 0.15
            assert result.frustration_level == 0.85
            assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_tier3_error_falls_back_to_tier2_result(self) -> None:
        """Test that cloud LLM error returns Tier 2 result, not neutral (AC #3).

        This validates the fix for HIGH Issue #2 - when cloud LLM fails,
        we should return the Tier 2 result instead of neutral 0.5.
        """
        # Setup mock cloud LLM that raises exception
        mock_cloud_client = AsyncMock()
        mock_cloud_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch("handoffkit.sentiment.analyzer.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.analyzer.TRANSFORMERS_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_cloud_client), \
             patch("handoffkit.sentiment.local_llm.TRANSFORMERS_AVAILABLE", True):

            config = SentimentConfig(
                enable_local_llm=True,
                enable_cloud_llm=True,
                cloud_llm_provider="openai",
                cloud_llm_api_key="test-key",
                cloud_llm_threshold=0.3,
                sentiment_threshold=0.5,
            )
            analyzer = SentimentAnalyzer(config=config)

            # Mock local LLM with specific low score
            tier2_result = SentimentResult(
                score=0.22,  # Below threshold, triggers Tier 3
                frustration_level=0.75,
                should_escalate=True,
                tier_used="local_llm",
                processing_time_ms=50.0,
            )
            mock_local_llm = AsyncMock()
            mock_local_llm.analyze = AsyncMock(return_value=tier2_result)
            analyzer._local_llm = mock_local_llm

            # Mock rule-based to trigger Tier 2
            mock_rule_based = AsyncMock()
            mock_rule_based.analyze = AsyncMock(
                return_value=SentimentResult(
                    score=0.45,  # Ambiguous - triggers Tier 2
                    frustration_level=0.5,
                    should_escalate=False,
                    tier_used="rule_based",
                    processing_time_ms=5.0,
                )
            )
            analyzer._rule_based = mock_rule_based

            msg = Message(speaker=MessageSpeaker.USER, content="Very frustrated!")
            result = await analyzer.analyze(msg)

            # Should return Tier 2 result, NOT neutral 0.5
            assert result.tier_used == "local_llm"
            assert result.score == 0.22  # Tier 2 result preserved
            assert result.frustration_level == 0.75
            assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_tier3_neutral_result_uses_tier2(self) -> None:
        """Test that neutral cloud result (error fallback) uses Tier 2 instead."""
        # Setup mock cloud LLM that returns neutral (error fallback)
        mock_cloud_response = MagicMock()
        mock_cloud_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"sentiment_score": 0.5, "frustration_level": 0.5, "should_escalate": false, "reasoning": "Neutral"}'
                )
            )
        ]
        mock_cloud_client = AsyncMock()
        mock_cloud_client.chat.completions.create = AsyncMock(return_value=mock_cloud_response)

        with patch("handoffkit.sentiment.analyzer.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.analyzer.TRANSFORMERS_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True), \
             patch("handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_cloud_client), \
             patch("handoffkit.sentiment.local_llm.TRANSFORMERS_AVAILABLE", True):

            config = SentimentConfig(
                enable_local_llm=True,
                enable_cloud_llm=True,
                cloud_llm_provider="openai",
                cloud_llm_api_key="test-key",
                cloud_llm_threshold=0.3,
                sentiment_threshold=0.5,
            )
            analyzer = SentimentAnalyzer(config=config)

            # Mock local LLM with low score
            tier2_result = SentimentResult(
                score=0.18,
                frustration_level=0.8,
                should_escalate=True,
                tier_used="local_llm",
                processing_time_ms=50.0,
            )
            mock_local_llm = AsyncMock()
            mock_local_llm.analyze = AsyncMock(return_value=tier2_result)
            analyzer._local_llm = mock_local_llm

            mock_rule_based = AsyncMock()
            mock_rule_based.analyze = AsyncMock(
                return_value=SentimentResult(
                    score=0.45,
                    frustration_level=0.5,
                    should_escalate=False,
                    tier_used="rule_based",
                    processing_time_ms=5.0,
                )
            )
            analyzer._rule_based = mock_rule_based

            msg = Message(speaker=MessageSpeaker.USER, content="Frustrated!")
            result = await analyzer.analyze(msg)

            # Should use Tier 2 when Tier 3 returns neutral (possible error)
            assert result.tier_used == "local_llm"
            assert result.score == 0.18


class TestCloudLLMSpecificErrors:
    """Tests for specific HTTP error handling (MEDIUM #6 fix)."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_429(self) -> None:
        """Test graceful handling of rate limit (429) error."""
        from httpx import HTTPStatusError, Request, Response

        mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_response = Response(429, request=mock_request)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=HTTPStatusError(
                "Rate limit exceeded", request=mock_request, response=mock_response
            )
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on rate limit
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_authentication_error_401(self) -> None:
        """Test graceful handling of authentication (401) error."""
        from httpx import HTTPStatusError, Request, Response

        mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_response = Response(401, request=mock_request)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=HTTPStatusError(
                "Invalid API key", request=mock_request, response=mock_response
            )
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="invalid-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on auth error
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_forbidden_error_403(self) -> None:
        """Test graceful handling of forbidden (403) error."""
        from httpx import HTTPStatusError, Request, Response

        mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_response = Response(403, request=mock_request)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=HTTPStatusError(
                "Forbidden", request=mock_request, response=mock_response
            )
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on forbidden error
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"

    @pytest.mark.asyncio
    async def test_network_error(self) -> None:
        """Test graceful handling of network connectivity error."""
        from httpx import ConnectError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=ConnectError("Connection refused")
        )

        with patch(
            "handoffkit.sentiment.cloud_llm.OPENAI_AVAILABLE", True
        ), patch(
            "handoffkit.sentiment.cloud_llm.AsyncOpenAI", return_value=mock_client
        ):
            analyzer = CloudLLMAnalyzer(provider="openai", api_key="test-key")
            await analyzer.initialize()

            msg = Message(speaker=MessageSpeaker.USER, content="Test message")
            result = await analyzer.analyze(msg)

            # Should return neutral result on network error
            assert result.score == 0.5
            assert result.tier_used == "cloud_llm"
