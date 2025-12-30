"""Sentiment analysis data models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SentimentTier(str, Enum):
    """Available sentiment analysis tiers."""

    RULE_BASED = "rule_based"
    LOCAL_LLM = "local_llm"
    CLOUD_LLM = "cloud_llm"


class SentimentFeatures(BaseModel):
    """Extracted features for sentiment scoring."""

    # Keyword-based features
    negative_keyword_count: int = 0
    positive_keyword_count: int = 0
    frustration_keyword_count: int = 0

    # Punctuation features
    exclamation_count: int = 0
    question_count: int = 0
    caps_ratio: float = Field(default=0.0, ge=0.0, le=1.0)

    # Frustration signal features (Story 2.6)
    caps_word_count: int = 0  # Count of ALL CAPS words (2+ chars)
    excessive_punctuation_count: int = 0  # Count of 3+ consecutive ! or ? patterns

    # Pattern features
    repeated_chars: bool = False
    contains_profanity: bool = False
    message_length: int = 0

    # Contextual features
    message_position: int = 0
    conversation_length: int = 0
    recent_negative_trend: float = Field(default=0.0, ge=-1.0, le=1.0)


class DegradationResult(BaseModel):
    """Result of conversation degradation analysis."""

    is_degrading: bool
    trend_value: float
    window_size: int
    scores: list[float]


class TierPerformance(BaseModel):
    """Performance metrics for a sentiment tier."""

    tier: SentimentTier
    avg_latency_ms: float = 0.0
    requests_count: int = 0
    error_count: int = 0
    accuracy_score: Optional[float] = None
