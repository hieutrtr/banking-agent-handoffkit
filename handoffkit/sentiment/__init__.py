"""HandoffKit Sentiment Analysis Module.

Contains sentiment analyzers with 3-tier architecture.
"""

from handoffkit.sentiment.analyzer import SentimentAnalyzer
from handoffkit.sentiment.cloud_llm import CloudLLMAnalyzer
from handoffkit.sentiment.local_llm import LocalLLMAnalyzer
from handoffkit.sentiment.models import SentimentFeatures, SentimentTier, TierPerformance
from handoffkit.sentiment.rule_based import RuleBasedAnalyzer

__all__ = [
    "SentimentAnalyzer",
    "RuleBasedAnalyzer",
    "LocalLLMAnalyzer",
    "CloudLLMAnalyzer",
    "SentimentTier",
    "SentimentFeatures",
    "TierPerformance",
]
