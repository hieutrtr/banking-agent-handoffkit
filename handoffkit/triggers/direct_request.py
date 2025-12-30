"""Direct request detection trigger."""

import re
import time
from typing import Any, Optional

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger
from handoffkit.utils.logging import get_logger


class DirectRequestTrigger(BaseTrigger):
    """Detects when users explicitly request human assistance.

    Uses NLP pattern matching to identify phrases like:
    - "Talk to a human"
    - "I need a real person"
    - "Connect me to an agent"
    - "Let me speak to someone"

    Target: <100ms evaluation time.
    """

    @property
    def trigger_name(self) -> str:
        return "direct_request"

    def __init__(self, patterns: Optional[list[str]] = None) -> None:
        """Initialize with optional custom patterns.

        Args:
            patterns: Optional list of regex patterns to use instead of defaults.
                     Patterns should be case-insensitive (use (?i) flag).
        """
        self._pattern_strings = patterns or self._default_patterns()
        # Pre-compile patterns for performance (Subtask 3.1)
        self._compiled_patterns = [
            re.compile(pattern) for pattern in self._pattern_strings
        ]
        # Pre-compile negative patterns (Task 2.4)
        self._compiled_negative_patterns = [
            re.compile(pattern) for pattern in self._default_negative_patterns()
        ]
        # Initialize logger (Task 4.1)
        self._logger = get_logger("trigger.direct_request")

    def _default_patterns(self) -> list[str]:
        """Return default patterns for human request detection."""
        return [
            # Basic talk/speak/connect patterns (using optional article a/an)
            r"(?i)\b(talk|speak|connect)\s+(to|with)\s+(an?\s+)?(human|person|agent|representative|someone|operator|support)",
            # Connect me to patterns
            r"(?i)\bconnect\s+me\s+(to|with)\s+(an?\s+)?(human|person|agent|representative|someone|operator|support)",
            # Need/want patterns
            r"(?i)\b(need|want)\s+(an?\s+)?(real|human|live)\s+(person|agent|help)",
            r"(?i)\b(need|want)\s+to\s+(talk|speak)\s+(to|with)\s+(an?\s+)?(human|person|agent|representative|someone|customer\s+support|support|supervisor|manager)",
            # Transfer patterns
            r"(?i)\btransfer\s+(me\s+)?(to\s+)?(an?\s+)?(human|agent|support)",
            r"(?i)\bplease\s+transfer\s+me",
            # Get me patterns
            r"(?i)\bget\s+me\s+(an?\s+)?(human|agent|person|operator|representative)",
            # Escalation patterns (Task 2.2)
            r"(?i)\b(need|want)\s+to\s+escalate",
            r"(?i)\bescalate\s+(this|my|the)",
            r"(?i)\b(talk|speak)\s+(to|with)\s+(an?\s+)?(supervisor|manager)",
            # Let me patterns
            r"(?i)\blet\s+me\s+(talk|speak)\s+(to|with)\s+(an?\s+)?(human|person|agent|representative|someone|supervisor|manager)",
            # Demand patterns (Task 2.3)
            r"(?i)\bi\s+demand\s+to\s+(talk|speak)",
        ]

    def _default_negative_patterns(self) -> list[str]:
        """Return patterns that indicate NOT requesting human assistance (Task 2.4)."""
        return [
            r"(?i)\b(don't|do\s+not|doesn't|does\s+not)\s+(need|want)\s+.*(human|agent|person|representative)",
            r"(?i)\b(no|not)\s+(need|asking)\s+.*(human|agent|person|representative)",
        ]

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate message for direct human request patterns.

        Args:
            message: The current message to evaluate.
            history: Previous messages in the conversation (unused for this trigger).
            context: Additional context for evaluation (unused for this trigger).

        Returns:
            TriggerResult indicating if a direct request pattern was detected.
        """
        # Start timing (Subtask 3.3)
        start_time = time.perf_counter()

        content = message.content

        # Log evaluation start (Task 4.2)
        message_preview = content[:50] + "..." if len(content) > 50 else content
        self._logger.debug(
            "Evaluating direct request trigger",
            extra={"message_preview": message_preview, "trigger_type": "direct_request"},
        )

        # Check negative patterns first to avoid false positives (Task 2.4)
        for pattern in self._compiled_negative_patterns:
            if pattern.search(content):
                # User explicitly said they don't need human help
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._logger.debug(
                    "Direct request trigger - negative pattern matched",
                    extra={
                        "triggered": False,
                        "confidence": 0.0,
                        "duration_ms": round(duration_ms, 2),
                        "trigger_type": "direct_request",
                    },
                )
                return TriggerResult(
                    triggered=False,
                    trigger_type=None,
                    confidence=0.0,
                    reason=None,
                    metadata={"duration_ms": round(duration_ms, 2)},
                )

        # Check each compiled pattern for a match (Subtask 1.2)
        for pattern in self._compiled_patterns:
            match = pattern.search(content)
            if match:
                # Early exit on first match (Subtask 3.2)
                duration_ms = (time.perf_counter() - start_time) * 1000
                reason = f"Matched direct request pattern: '{match.group()}'"

                # Log trigger result (Task 4.3)
                self._logger.debug(
                    "Direct request trigger - pattern matched",
                    extra={
                        "triggered": True,
                        "confidence": 0.9,
                        "reason": reason,
                        "duration_ms": round(duration_ms, 2),
                        "trigger_type": "direct_request",
                    },
                )

                # Return with high confidence (Subtask 1.3)
                return TriggerResult(
                    triggered=True,
                    trigger_type=TriggerType.DIRECT_REQUEST,
                    confidence=0.9,
                    reason=reason,
                    metadata={"duration_ms": round(duration_ms, 2)},
                )

        # No match found (Subtask 1.4)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log timing (Task 4.4)
        self._logger.debug(
            "Direct request trigger - no match",
            extra={
                "triggered": False,
                "confidence": 0.0,
                "duration_ms": round(duration_ms, 2),
                "trigger_type": "direct_request",
            },
        )

        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            reason=None,
            metadata={"duration_ms": round(duration_ms, 2)},
        )
