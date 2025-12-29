"""Critical keyword monitoring trigger."""

from typing import Any, Optional

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger


class KeywordTrigger(BaseTrigger):
    """Monitors for critical keywords requiring immediate escalation.

    Default categories:
    - Financial: fraud, unauthorized, stolen, dispute
    - Safety: emergency, threat, danger, harm
    - Legal: lawsuit, attorney, lawyer, legal action
    - Urgency: urgent, immediately, asap, right now

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
            keywords: List of keywords to monitor.
            case_sensitive: Whether matching is case-sensitive.
        """
        self._keywords = keywords or self._default_keywords()
        self._case_sensitive = case_sensitive

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
        ]

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate message for critical keywords."""
        raise NotImplementedError("KeywordTrigger evaluation pending")
