"""Critical keyword monitoring trigger."""

import re
import time
from typing import Any, Optional

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger
from handoffkit.utils.logging import get_logger


class KeywordTrigger(BaseTrigger):
    """Monitors for critical keywords requiring immediate escalation.

    Default categories:
    - Financial: fraud, unauthorized, stolen, dispute, chargeback
    - Safety: emergency, threat, danger, harm, suicide, crisis
    - Legal: lawsuit, attorney, lawyer, legal action, sue
    - Urgency: urgent, immediately, asap, right now, critical
    - Access: locked out, locked account, cannot access

    Target: <50ms evaluation time.
    """

    @property
    def trigger_name(self) -> str:
        return "keyword"

    def __init__(
        self,
        keywords: Optional[list[str]] = None,
        case_sensitive: bool = False,
    ) -> None:
        """Initialize with keyword list.

        Args:
            keywords: List of keywords to monitor. If None, uses default keywords.
            case_sensitive: Whether matching is case-sensitive.
        """
        self._keywords = keywords if keywords is not None else self._default_keywords()
        self._case_sensitive = case_sensitive
        self._logger = get_logger("trigger.keyword")

        # Pre-compile patterns for performance (Subtask 1.2)
        self._compiled_patterns = self._compile_patterns()

    def _default_keywords(self) -> list[str]:
        """Return default critical keywords."""
        return [
            # Financial
            "fraud", "unauthorized", "stolen", "dispute", "chargeback",
            # Safety
            "emergency", "threat", "danger", "harm", "suicide", "crisis",
            # Legal
            "lawsuit", "attorney", "lawyer", "legal action", "sue",
            # Urgency
            "urgent", "immediately", "asap", "right now", "critical",
            # Access
            "locked out", "locked account", "cannot access",
        ]

    def _compile_patterns(self) -> list[tuple[re.Pattern[str], str]]:
        """Compile keyword patterns with word boundaries.

        Returns:
            List of tuples (compiled_pattern, original_keyword).
        """
        patterns = []
        flags = 0 if self._case_sensitive else re.IGNORECASE

        for keyword in self._keywords:
            # Escape special regex characters in the keyword
            escaped = re.escape(keyword)
            # Handle multi-word phrases by allowing flexible whitespace
            escaped = escaped.replace(r"\ ", r"\s+")
            # Create pattern with word boundaries
            pattern_str = rf"\b{escaped}\b"
            compiled = re.compile(pattern_str, flags)
            patterns.append((compiled, keyword))

        return patterns

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate message for critical keywords.

        Args:
            message: The current message to evaluate.
            history: Previous messages in the conversation (unused for this trigger).
            context: Additional context for evaluation (unused for this trigger).

        Returns:
            TriggerResult indicating if a critical keyword was detected.
        """
        start_time = time.perf_counter()
        content = message.content

        # Log evaluation start (Subtask 5.2)
        message_preview = content[:50] + "..." if len(content) > 50 else content
        self._logger.debug(
            "Evaluating keyword trigger",
            extra={"message_preview": message_preview, "trigger_type": "keyword"},
        )

        # Check each keyword pattern (Subtask 1.3)
        for pattern, keyword in self._compiled_patterns:
            if pattern.search(content):
                # Early exit on first match
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log matched keyword (Subtask 5.3)
                self._logger.debug(
                    "Keyword trigger - matched",
                    extra={
                        "triggered": True,
                        "confidence": 0.95,
                        "matched_keyword": keyword,
                        "duration_ms": round(duration_ms, 2),
                        "trigger_type": "keyword",
                    },
                )

                # Return with high confidence (Subtask 1.4)
                return TriggerResult(
                    triggered=True,
                    trigger_type=TriggerType.CRITICAL_KEYWORD,
                    confidence=0.95,
                    reason=f"Matched critical keyword: '{keyword}'",
                    metadata={
                        "duration_ms": round(duration_ms, 2),
                        "matched_keyword": keyword,
                        "priority": "immediate",
                    },
                )

        # No match found (Subtask 1.5)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log no match (Subtask 5.3)
        self._logger.debug(
            "Keyword trigger - no match",
            extra={
                "triggered": False,
                "confidence": 0.0,
                "duration_ms": round(duration_ms, 2),
                "trigger_type": "keyword",
            },
        )

        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            reason=None,
            metadata={"duration_ms": round(duration_ms, 2)},
        )
