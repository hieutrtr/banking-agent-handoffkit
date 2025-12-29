"""Tests for HandoffKit configuration models."""

import pytest
from pydantic import ValidationError

from handoffkit import (
    HandoffConfig,
    TriggerConfig,
    SentimentConfig,
    RoutingConfig,
    IntegrationConfig,
)


class TestTriggerConfig:
    """Test TriggerConfig model validation."""

    def test_default_values(self):
        """Test default values match specification."""
        config = TriggerConfig()
        assert config.direct_request_enabled is True
        assert config.failure_threshold == 3
        assert config.sentiment_threshold == 0.3
        assert config.critical_keywords == []
        assert config.custom_rules_enabled is False

    def test_failure_threshold_range_valid(self):
        """Test valid failure_threshold values (1-5)."""
        config1 = TriggerConfig(failure_threshold=1)
        assert config1.failure_threshold == 1

        config5 = TriggerConfig(failure_threshold=5)
        assert config5.failure_threshold == 5

    def test_failure_threshold_below_min(self):
        """Test failure_threshold below minimum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TriggerConfig(failure_threshold=0)

        assert "failure_threshold" in str(exc_info.value).lower()

    def test_failure_threshold_above_max(self):
        """Test failure_threshold above maximum (5) raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TriggerConfig(failure_threshold=6)

        assert "failure_threshold" in str(exc_info.value).lower()

    def test_sentiment_threshold_range(self):
        """Test sentiment_threshold valid range (0.0-1.0)."""
        config0 = TriggerConfig(sentiment_threshold=0.0)
        assert config0.sentiment_threshold == 0.0

        config1 = TriggerConfig(sentiment_threshold=1.0)
        assert config1.sentiment_threshold == 1.0

        config_mid = TriggerConfig(sentiment_threshold=0.5)
        assert config_mid.sentiment_threshold == 0.5

    def test_sentiment_threshold_out_of_range(self):
        """Test sentiment_threshold outside range raises error."""
        with pytest.raises(ValidationError):
            TriggerConfig(sentiment_threshold=-0.1)

        with pytest.raises(ValidationError):
            TriggerConfig(sentiment_threshold=1.1)

    def test_critical_keywords_list(self):
        """Test critical_keywords accepts list of strings."""
        keywords = ["fraud", "emergency", "stolen"]
        config = TriggerConfig(critical_keywords=keywords)
        assert config.critical_keywords == keywords
        assert len(config.critical_keywords) == 3

    def test_immutability(self):
        """Test config is immutable after creation."""
        config = TriggerConfig()
        with pytest.raises(ValidationError):
            config.failure_threshold = 5

    def test_model_copy_for_modification(self):
        """Test model_copy can create modified version."""
        config = TriggerConfig()
        new_config = config.model_copy(update={"failure_threshold": 2})
        assert config.failure_threshold == 3  # Original unchanged
        assert new_config.failure_threshold == 2


class TestSentimentConfig:
    """Test SentimentConfig model validation."""

    def test_default_values(self):
        """Test default values."""
        config = SentimentConfig()
        assert config.tier == "rule_based"
        assert config.frustration_threshold == 0.7
        assert config.escalation_threshold == 0.8

    def test_tier_valid_values(self):
        """Test valid tier values."""
        for tier in ["rule_based", "local_llm", "cloud_llm"]:
            config = SentimentConfig(tier=tier)
            assert config.tier == tier

    def test_tier_invalid_value(self):
        """Test invalid tier raises error."""
        with pytest.raises(ValidationError):
            SentimentConfig(tier="invalid_tier")

    def test_threshold_ranges(self):
        """Test threshold ranges are validated."""
        config = SentimentConfig(frustration_threshold=0.5, escalation_threshold=0.9)
        assert config.frustration_threshold == 0.5
        assert config.escalation_threshold == 0.9

    def test_immutability(self):
        """Test config is immutable."""
        config = SentimentConfig()
        with pytest.raises(ValidationError):
            config.tier = "cloud_llm"


class TestRoutingConfig:
    """Test RoutingConfig model validation."""

    def test_default_values(self):
        """Test default values."""
        config = RoutingConfig()
        assert config.strategy == "round_robin"
        assert config.fallback_queue is None
        assert config.availability_cache_ttl == 30

    def test_strategy_valid_values(self):
        """Test valid strategy values."""
        for strategy in ["round_robin", "least_busy", "skill_based"]:
            config = RoutingConfig(strategy=strategy)
            assert config.strategy == strategy

    def test_strategy_invalid_value(self):
        """Test invalid strategy raises error."""
        with pytest.raises(ValidationError):
            RoutingConfig(strategy="random")

    def test_availability_cache_ttl_range(self):
        """Test cache TTL range (5-300)."""
        config_min = RoutingConfig(availability_cache_ttl=5)
        assert config_min.availability_cache_ttl == 5

        config_max = RoutingConfig(availability_cache_ttl=300)
        assert config_max.availability_cache_ttl == 300

    def test_availability_cache_ttl_out_of_range(self):
        """Test cache TTL outside range raises error."""
        with pytest.raises(ValidationError):
            RoutingConfig(availability_cache_ttl=4)

        with pytest.raises(ValidationError):
            RoutingConfig(availability_cache_ttl=301)

    def test_immutability(self):
        """Test config is immutable."""
        config = RoutingConfig()
        with pytest.raises(ValidationError):
            config.strategy = "least_busy"


class TestIntegrationConfig:
    """Test IntegrationConfig model validation."""

    def test_default_values(self):
        """Test default values."""
        config = IntegrationConfig()
        assert config.provider == "zendesk"
        assert config.api_key is None
        assert config.api_url is None
        assert config.extra == {}

    def test_provider_valid_values(self):
        """Test valid provider values."""
        for provider in ["zendesk", "intercom", "custom"]:
            config = IntegrationConfig(provider=provider)
            assert config.provider == provider

    def test_provider_invalid_value(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValidationError):
            IntegrationConfig(provider="salesforce")

    def test_with_credentials(self):
        """Test with API credentials."""
        config = IntegrationConfig(
            provider="zendesk",
            api_key="secret-key-123",
            api_url="https://mycompany.zendesk.com/api",
        )
        assert config.api_key == "secret-key-123"
        assert config.api_url == "https://mycompany.zendesk.com/api"

    def test_extra_settings(self):
        """Test extra provider-specific settings."""
        config = IntegrationConfig(
            provider="zendesk",
            extra={"subdomain": "mycompany", "timeout": 30},
        )
        assert config.extra["subdomain"] == "mycompany"
        assert config.extra["timeout"] == 30

    def test_immutability(self):
        """Test config is immutable."""
        config = IntegrationConfig()
        with pytest.raises(ValidationError):
            config.provider = "intercom"


class TestHandoffConfig:
    """Test HandoffConfig main configuration model."""

    def test_default_values(self):
        """Test default values match specification."""
        config = HandoffConfig()
        assert config.max_context_messages == 100
        assert config.max_context_size_kb == 50
        assert config.summary_max_words == 200

    def test_nested_config_defaults(self):
        """Test nested configs have correct defaults."""
        config = HandoffConfig()
        assert config.triggers.failure_threshold == 3
        assert config.triggers.sentiment_threshold == 0.3
        assert config.sentiment.tier == "rule_based"
        assert config.routing.strategy == "round_robin"
        assert config.integration.provider == "zendesk"

    def test_custom_nested_configs(self):
        """Test providing custom nested configs."""
        config = HandoffConfig(
            triggers=TriggerConfig(failure_threshold=2),
            sentiment=SentimentConfig(tier="local_llm"),
        )
        assert config.triggers.failure_threshold == 2
        assert config.sentiment.tier == "local_llm"

    def test_max_context_messages_range(self):
        """Test max_context_messages range (1-500)."""
        config_min = HandoffConfig(max_context_messages=1)
        assert config_min.max_context_messages == 1

        config_max = HandoffConfig(max_context_messages=500)
        assert config_max.max_context_messages == 500

    def test_max_context_messages_out_of_range(self):
        """Test max_context_messages outside range raises error."""
        with pytest.raises(ValidationError):
            HandoffConfig(max_context_messages=0)

        with pytest.raises(ValidationError):
            HandoffConfig(max_context_messages=501)

    def test_max_context_size_kb_range(self):
        """Test max_context_size_kb range (10-200)."""
        config_min = HandoffConfig(max_context_size_kb=10)
        assert config_min.max_context_size_kb == 10

        config_max = HandoffConfig(max_context_size_kb=200)
        assert config_max.max_context_size_kb == 200

    def test_summary_max_words_range(self):
        """Test summary_max_words range (50-500)."""
        config_min = HandoffConfig(summary_max_words=50)
        assert config_min.summary_max_words == 50

        config_max = HandoffConfig(summary_max_words=500)
        assert config_max.summary_max_words == 500

    def test_immutability(self):
        """Test config is immutable after creation."""
        config = HandoffConfig()
        with pytest.raises(ValidationError):
            config.max_context_messages = 50

    def test_model_copy_for_modification(self):
        """Test model_copy creates new config with changes."""
        config = HandoffConfig()
        new_config = config.model_copy(
            update={
                "max_context_messages": 50,
                "triggers": TriggerConfig(failure_threshold=2),
            }
        )

        # Original unchanged
        assert config.max_context_messages == 100
        assert config.triggers.failure_threshold == 3

        # New config has changes
        assert new_config.max_context_messages == 50
        assert new_config.triggers.failure_threshold == 2


class TestValidationErrorMessages:
    """Test that validation errors are helpful and actionable."""

    def test_trigger_threshold_error_message(self):
        """Test failure_threshold error message is informative."""
        with pytest.raises(ValidationError) as exc_info:
            TriggerConfig(failure_threshold=10)

        error_str = str(exc_info.value)
        # Should mention the constraint
        assert "5" in error_str or "less than" in error_str.lower()

    def test_sentiment_threshold_error_message(self):
        """Test sentiment_threshold error message is informative."""
        with pytest.raises(ValidationError) as exc_info:
            TriggerConfig(sentiment_threshold=2.0)

        error_str = str(exc_info.value)
        assert "1" in error_str or "less than" in error_str.lower()

    def test_invalid_tier_error_message(self):
        """Test tier validation error mentions valid options."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentConfig(tier="invalid")

        error_str = str(exc_info.value)
        # Pattern validation should indicate what's expected
        assert "pattern" in error_str.lower() or "rule_based" in error_str.lower() or "match" in error_str.lower()
