"""Direct request detection trigger."""

from typing import Any, Optional

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger


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
        """Initialize with optional custom patterns."""
        self._patterns = patterns or self._default_patterns()

    def _default_patterns(self) -> list[str]:
        """Return default patterns for human request detection."""
        return [
            r"(?i)\b(talk|speak|connect)\s+(to|with)\s+(a\s+)?(human|person|agent|representative|someone)",
            r"(?i)\b(need|want)\s+(a\s+)?(real|human|live)\s+(person|agent|help)",
            r"(?i)\btransfer\s+(me\s+)?(to\s+)?(a\s+)?(human|agent|support)",
            r"(?i)\bget\s+me\s+(a\s+)?(human|agent|person)",
        ]

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate message for direct human request patterns."""
        raise NotImplementedError("DirectRequestTrigger evaluation pending")
