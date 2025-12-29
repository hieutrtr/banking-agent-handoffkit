"""HandoffKit Configuration Management."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TriggerConfig(BaseModel):
    """Configuration for handoff triggers."""

    direct_request_enabled: bool = True
    failure_threshold: int = Field(default=3, ge=1, le=10)
    critical_keywords: list[str] = Field(default_factory=list)
    custom_rules_enabled: bool = False


class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis."""

    tier: str = Field(default="rule_based", pattern="^(rule_based|local_llm|cloud_llm)$")
    frustration_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    escalation_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class RoutingConfig(BaseModel):
    """Configuration for agent routing."""

    strategy: str = Field(default="round_robin", pattern="^(round_robin|least_busy|skill_based)$")
    fallback_queue: Optional[str] = None
    availability_cache_ttl: int = Field(default=30, ge=5, le=300)


class IntegrationConfig(BaseModel):
    """Configuration for helpdesk integrations."""

    provider: str = Field(default="zendesk", pattern="^(zendesk|intercom|custom)$")
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class HandoffConfig(BaseModel):
    """Main configuration for HandoffKit."""

    triggers: TriggerConfig = Field(default_factory=TriggerConfig)
    sentiment: SentimentConfig = Field(default_factory=SentimentConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    integration: IntegrationConfig = Field(default_factory=IntegrationConfig)

    max_context_messages: int = Field(default=100, ge=1, le=500)
    max_context_size_kb: int = Field(default=50, ge=10, le=200)
    summary_max_words: int = Field(default=200, ge=50, le=500)
