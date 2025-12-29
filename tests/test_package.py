"""Test package structure and imports."""

import pytest


class TestPackageImports:
    """Test that all package imports work correctly."""

    def test_import_handoffkit(self):
        """Test main package import."""
        import handoffkit

        assert hasattr(handoffkit, "__version__")
        assert handoffkit.__version__ == "0.1.0"

    def test_import_core_classes(self):
        """Test core class imports."""
        from handoffkit import (
            HandoffConfig,
            HandoffOrchestrator,
            Message,
            ConversationContext,
            HandoffDecision,
            HandoffResult,
        )

        assert HandoffConfig is not None
        assert HandoffOrchestrator is not None
        assert Message is not None
        assert ConversationContext is not None
        assert HandoffDecision is not None
        assert HandoffResult is not None

    def test_import_config_classes(self):
        """Test configuration class imports."""
        from handoffkit import (
            TriggerConfig,
            SentimentConfig,
            RoutingConfig,
            IntegrationConfig,
        )

        assert TriggerConfig is not None
        assert SentimentConfig is not None
        assert RoutingConfig is not None
        assert IntegrationConfig is not None

    def test_import_exceptions(self):
        """Test exception imports."""
        from handoffkit import (
            HandoffKitError,
            ConfigurationError,
            TriggerError,
            SentimentAnalysisError,
            ContextPackagingError,
            RoutingError,
            IntegrationError,
            RateLimitError,
            AuthenticationError,
        )

        assert issubclass(ConfigurationError, HandoffKitError)
        assert issubclass(TriggerError, HandoffKitError)
        assert issubclass(SentimentAnalysisError, HandoffKitError)

    def test_import_enums(self):
        """Test enum imports."""
        from handoffkit import (
            HandoffPriority,
            HandoffStatus,
            TriggerType,
        )

        assert HandoffPriority.HIGH.value == "high"
        assert HandoffStatus.PENDING.value == "pending"
        assert TriggerType.DIRECT_REQUEST.value == "direct_request"


class TestSubpackageImports:
    """Test subpackage imports."""

    def test_import_triggers(self):
        """Test triggers subpackage imports."""
        from handoffkit.triggers import (
            BaseTrigger,
            DirectRequestTrigger,
            FailureTrackingTrigger,
            KeywordTrigger,
            CustomRuleTrigger,
            TriggerFactory,
        )

        assert BaseTrigger is not None
        assert DirectRequestTrigger is not None
        assert TriggerFactory is not None

    def test_import_sentiment(self):
        """Test sentiment subpackage imports."""
        from handoffkit.sentiment import (
            SentimentAnalyzer,
            RuleBasedAnalyzer,
            LocalLLMAnalyzer,
            CloudLLMAnalyzer,
            SentimentTier,
        )

        assert SentimentAnalyzer is not None
        assert SentimentTier.RULE_BASED.value == "rule_based"

    def test_import_context(self):
        """Test context subpackage imports."""
        from handoffkit.context import ContextPackager
        from handoffkit.context.adapters import (
            BaseAdapter,
            JSONAdapter,
            MarkdownAdapter,
        )

        assert ContextPackager is not None
        assert JSONAdapter is not None

    def test_import_routing(self):
        """Test routing subpackage imports."""
        from handoffkit.routing import (
            AgentRouter,
            BaseStrategy,
            RoundRobinStrategy,
        )

        assert AgentRouter is not None
        assert RoundRobinStrategy is not None

    def test_import_integrations(self):
        """Test integrations subpackage imports."""
        from handoffkit.integrations import BaseIntegration
        from handoffkit.integrations.zendesk import ZendeskIntegration
        from handoffkit.integrations.intercom import IntercomIntegration

        assert BaseIntegration is not None
        assert ZendeskIntegration is not None
        assert IntercomIntegration is not None

    def test_import_utils(self):
        """Test utils subpackage imports."""
        from handoffkit.utils import (
            get_logger,
            configure_logging,
            validate_api_key,
            validate_url,
        )

        assert get_logger is not None
        assert configure_logging is not None


class TestDefaultConfig:
    """Test default configuration values."""

    def test_default_handoff_config(self):
        """Test HandoffConfig has correct defaults."""
        from handoffkit import HandoffConfig

        config = HandoffConfig()

        assert config.max_context_messages == 100
        assert config.max_context_size_kb == 50
        assert config.summary_max_words == 200

    def test_default_trigger_config(self):
        """Test TriggerConfig has correct defaults."""
        from handoffkit import TriggerConfig

        config = TriggerConfig()

        assert config.direct_request_enabled is True
        assert config.failure_threshold == 3
        assert config.custom_rules_enabled is False

    def test_default_sentiment_config(self):
        """Test SentimentConfig has correct defaults."""
        from handoffkit import SentimentConfig

        config = SentimentConfig()

        assert config.tier == "rule_based"
        assert config.frustration_threshold == 0.7
        assert config.escalation_threshold == 0.8

    def test_default_routing_config(self):
        """Test RoutingConfig has correct defaults."""
        from handoffkit import RoutingConfig

        config = RoutingConfig()

        assert config.strategy == "round_robin"
        assert config.availability_cache_ttl == 30


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_message_creation(self):
        """Test Message model creation."""
        from handoffkit import Message

        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_conversation_context_creation(self):
        """Test ConversationContext model creation."""
        from handoffkit import ConversationContext, Message

        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            messages=[Message(role="user", content="Hello")],
        )

        assert context.conversation_id == "conv-123"
        assert context.user_id == "user-456"
        assert len(context.messages) == 1

    def test_config_validation(self):
        """Test configuration validation."""
        from handoffkit import TriggerConfig
        from pydantic import ValidationError

        # Valid config
        config = TriggerConfig(failure_threshold=5)
        assert config.failure_threshold == 5

        # Invalid config should raise ValidationError
        with pytest.raises(ValidationError):
            TriggerConfig(failure_threshold=20)  # Max is 10
