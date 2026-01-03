"""HandoffKit Configuration Management.

This module provides configuration classes for HandoffKit, including:
- TriggerConfig: Settings for handoff trigger detection
- SentimentConfig: Settings for sentiment analysis
- RoutingConfig: Settings for agent routing
- IntegrationConfig: Settings for helpdesk integrations
- HandoffConfig: Main configuration combining all settings

All configuration models are immutable after creation. To modify config,
use the model_copy(update={...}) method to create a new instance.

Example usage:
    >>> from handoffkit import HandoffConfig, TriggerConfig
    >>> config = HandoffConfig()
    >>> # Create modified copy
    >>> new_config = config.model_copy(
    ...     update={"triggers": TriggerConfig(failure_threshold=2)}
    ... )
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TriggerConfig(BaseModel):
    """Configuration for handoff triggers.

    Attributes:
        direct_request_enabled: Enable detection of explicit human agent requests
        failure_threshold: Number of consecutive failures before triggering (1-5)
        sentiment_threshold: Sentiment score threshold for escalation (0.0-1.0)
        critical_keywords: List of keywords that trigger immediate handoff
        custom_rules_enabled: Enable custom trigger rules

    Example:
        >>> config = TriggerConfig(failure_threshold=2, sentiment_threshold=0.4)
        >>> config.failure_threshold
        2
    """

    model_config = ConfigDict(frozen=True)

    direct_request_enabled: bool = Field(
        default=True,
        description="Enable detection of explicit human agent requests",
    )
    failure_threshold: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of consecutive AI failures before triggering handoff (1-5)",
    )
    sentiment_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sentiment score threshold for escalation (0.0-1.0, lower = more negative)",
    )
    critical_keywords: list[str] = Field(
        default_factory=list,
        description="List of keywords that trigger immediate handoff",
    )
    custom_rules_enabled: bool = Field(
        default=False,
        description="Enable custom trigger rules",
    )


class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis.

    Attributes:
        tier: Analysis tier to use ('rule_based', 'local_llm', 'cloud_llm')
        sentiment_threshold: Sentiment score threshold for escalation (0.0-1.0)
        frustration_threshold: Frustration level threshold for escalation (0.0-1.0)
        escalation_threshold: Overall threshold for automatic escalation (0.0-1.0)
        enable_local_llm: Whether to enable Tier 2 (local LLM) analysis
        financial_domain: Whether to use FinBERT for financial domain text
        enable_cloud_llm: Whether to enable Tier 3 (cloud LLM) analysis
        cloud_llm_provider: Cloud LLM provider ('openai' or 'anthropic')
        cloud_llm_api_key: API key for cloud LLM provider
        cloud_llm_model: Model to use for cloud LLM analysis
        cloud_llm_threshold: Escalate to cloud LLM when local score below this

    Example:
        >>> config = SentimentConfig(tier="local_llm", enable_local_llm=True)
        >>> config.tier
        'local_llm'
        >>> config.enable_local_llm
        True
        >>> # Enable cloud LLM
        >>> cloud_config = SentimentConfig(
        ...     enable_cloud_llm=True,
        ...     cloud_llm_provider="openai",
        ...     cloud_llm_api_key="sk-...",
        ... )
    """

    model_config = ConfigDict(frozen=True)

    tier: str = Field(
        default="rule_based",
        pattern="^(rule_based|local_llm|cloud_llm)$",
        description="Analysis tier: 'rule_based', 'local_llm', or 'cloud_llm'",
    )
    sentiment_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sentiment score threshold for escalation (0.0-1.0)",
    )
    frustration_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Frustration level threshold for escalation (0.0-1.0)",
    )
    escalation_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Overall threshold for automatic escalation (0.0-1.0)",
    )
    enable_local_llm: bool = Field(
        default=False,
        description="Enable Tier 2 (local LLM) sentiment analysis",
    )
    financial_domain: bool = Field(
        default=False,
        description="Use FinBERT for financial domain-specific sentiment analysis",
    )

    # Cloud LLM Settings (Tier 3)
    enable_cloud_llm: bool = Field(
        default=False,
        description="Enable Tier 3 (cloud LLM) sentiment analysis",
    )
    cloud_llm_provider: Optional[str] = Field(
        default=None,
        pattern="^(openai|anthropic)$",
        description="Cloud LLM provider: 'openai' or 'anthropic'",
    )
    cloud_llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for cloud LLM provider",
    )
    cloud_llm_model: str = Field(
        default="gpt-4o-mini",
        description="Model to use for cloud LLM analysis",
    )
    cloud_llm_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Escalate to cloud LLM when local score below this threshold",
    )


class RoutingConfig(BaseModel):
    """Configuration for agent routing.

    Attributes:
        strategy: Routing strategy ('round_robin', 'least_busy', 'skill_based')
        fallback_queue: Queue name when no agents available
        availability_cache_ttl: Seconds to cache agent availability (5-300)

    Example:
        >>> config = RoutingConfig(strategy="least_busy")
        >>> config.strategy
        'least_busy'
    """

    model_config = ConfigDict(frozen=True)

    strategy: str = Field(
        default="round_robin",
        pattern="^(round_robin|least_busy|skill_based)$",
        description="Routing strategy: 'round_robin', 'least_busy', or 'skill_based'",
    )
    fallback_queue: Optional[str] = Field(
        default=None,
        description="Queue name to use when no agents are available",
    )
    availability_cache_ttl: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Seconds to cache agent availability data (5-300)",
    )


class IntegrationConfig(BaseModel):
    """Configuration for helpdesk integrations.

    Attributes:
        provider: Helpdesk provider ('zendesk', 'intercom', 'custom')
        api_key: API key for the provider
        api_url: Base URL for the provider API
        extra: Additional provider-specific settings

    Example:
        >>> config = IntegrationConfig(provider="zendesk", api_key="key123")
        >>> config.provider
        'zendesk'
    """

    model_config = ConfigDict(frozen=True)

    provider: str = Field(
        default="zendesk",
        pattern="^(zendesk|intercom|custom)$",
        description="Helpdesk provider: 'zendesk', 'intercom', or 'custom'",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the helpdesk provider",
    )
    api_url: Optional[str] = Field(
        default=None,
        description="Base URL for the provider API",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific settings",
    )


class HandoffConfig(BaseModel):
    """Main configuration for HandoffKit.

    This is the primary configuration class that combines all subsystem
    configurations. All fields have sensible defaults for quick start.

    Attributes:
        triggers: Trigger detection configuration
        sentiment: Sentiment analysis configuration
        routing: Agent routing configuration
        integration: Helpdesk integration configuration
        max_context_messages: Maximum messages to include in context (1-500)
        max_context_size_kb: Maximum context size in KB (10-200)
        summary_max_words: Maximum words in conversation summary (50-500)

    Example:
        >>> config = HandoffConfig()
        >>> config.triggers.failure_threshold
        3
        >>> # Create a modified copy
        >>> new_config = config.model_copy(
        ...     update={"triggers": TriggerConfig(failure_threshold=2)}
        ... )
    """

    model_config = ConfigDict(frozen=True)

    triggers: TriggerConfig = Field(
        default_factory=TriggerConfig,
        description="Trigger detection configuration",
    )
    sentiment: SentimentConfig = Field(
        default_factory=SentimentConfig,
        description="Sentiment analysis configuration",
    )
    routing: RoutingConfig = Field(
        default_factory=RoutingConfig,
        description="Agent routing configuration",
    )
    integration: IntegrationConfig = Field(
        default_factory=IntegrationConfig,
        description="Helpdesk integration configuration",
    )

    max_context_messages: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of messages to include in handoff context",
    )
    max_context_size_kb: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum size of context package in kilobytes",
    )
    summary_max_words: int = Field(
        default=200,
        ge=50,
        le=500,
        description="Maximum words in AI-generated conversation summary",
    )
