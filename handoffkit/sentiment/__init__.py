"""HandoffKit Sentiment Analysis Module.

Contains sentiment analyzers with 3-tier architecture.
"""

from handoffkit.sentiment.analyzer import SentimentAnalyzer
from handoffkit.sentiment.cloud_llm import (
    CloudLLMAnalyzer,
    OPENAI_AVAILABLE,
    ANTHROPIC_AVAILABLE,
)
from handoffkit.sentiment.degradation import DegradationTracker
from handoffkit.sentiment.local_llm import LocalLLMAnalyzer, TRANSFORMERS_AVAILABLE
from handoffkit.sentiment.models import (
    DegradationResult,
    SentimentFeatures,
    SentimentTier,
    TierPerformance,
)
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer

__all__ = [
    "SentimentAnalyzer",
    "RuleBasedAnalyzer",
    "LocalLLMAnalyzer",
    "CloudLLMAnalyzer",
    "DegradationTracker",
    "DegradationResult",
    "SentimentTier",
    "SentimentFeatures",
    "TierPerformance",
    # Availability flags for conditional import detection
    "TRANSFORMERS_AVAILABLE",
    "OPENAI_AVAILABLE",
    "ANTHROPIC_AVAILABLE",
]
