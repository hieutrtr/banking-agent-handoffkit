"""Failure pattern tracking trigger."""

import re
import time
from typing import Any, Optional

from handoffkit.core.types import Message, MessageSpeaker, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger
from handoffkit.utils.logging import get_logger


class FailureTrackingTrigger(BaseTrigger):
    """Tracks consecutive AI response failures to trigger handoff.

    Monitors for:
    - "I don't understand" responses from AI
    - User expressing confusion/frustration with answers
    - Repeated similar questions (rephrasing)
    - Bot loop detection

    Default threshold: 2-3 consecutive failures.
    """

    @property
    def trigger_name(self) -> str:
        return "failure_tracking"

    def __init__(
        self,
        failure_threshold: int = 3,
        failure_window: int = 5,
    ) -> None:
        """Initialize with configurable thresholds.

        Args:
            failure_threshold: Number of failures to trigger handoff.
            failure_window: Number of recent messages to analyze.
        """
        self._threshold = failure_threshold
        self._window = failure_window
        self._logger = get_logger("trigger.failure_tracking")

        # Pre-compile AI failure patterns (Subtask 2.1)
        self._ai_failure_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"i don'?t understand",
                r"i'?m not sure",
                r"i cannot help with that",
                r"could you please rephrase",
                r"i'?m having trouble understanding",
                r"i don'?t know",
                r"i'?m unable to",
                r"i can'?t help with",
            ]
        ]

        # Pre-compile user frustration patterns (Subtask 2.2)
        self._user_frustration_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"you'?re not helping",
                r"that'?s not what i asked",
                r"i already (told|said|explained)",
                r"you keep saying the same thing",
                r"this doesn'?t work",
                r"that doesn'?t (help|work|answer)",
                r"you'?re not (listening|understanding)",
                r"i just (told|said|asked) you",
            ]
        ]

        # Pre-compile success patterns (Subtask 3.1)
        self._success_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"\bthanks?\b",
                r"\bthank you\b",
                r"\bthat helps?\b",
                r"\bthat worked\b",
                r"\bperfect\b",
                r"\bgreat\b",
                r"\bgot it\b",
                r"\bunderstood\b",
                r"\bawesome\b",
                r"\bexactly\b",
                r"\bexcellent\b",
            ]
        ]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts.

        Args:
            text1: First text to compare.
            text2: Second text to compare.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        # Tokenize: split by whitespace, lowercase, filter short words
        words1 = set(
            word.lower().strip(".,!?;:'\"")
            for word in text1.split()
            if len(word) > 2
        )
        words2 = set(
            word.lower().strip(".,!?;:'\"")
            for word in text2.split()
            if len(word) > 2
        )

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _is_ai_failure(self, content: str) -> bool:
        """Check if AI response indicates failure.

        Args:
            content: The AI message content.

        Returns:
            True if the response indicates failure.
        """
        for pattern in self._ai_failure_patterns:
            if pattern.search(content):
                return True
        return False

    def _is_user_frustration(self, content: str) -> bool:
        """Check if user message indicates frustration.

        Args:
            content: The user message content.

        Returns:
            True if the message indicates frustration.
        """
        for pattern in self._user_frustration_patterns:
            if pattern.search(content):
                return True
        return False

    def _is_success_indicator(self, content: str) -> bool:
        """Check if message indicates success/satisfaction.

        Args:
            content: The message content.

        Returns:
            True if the message indicates success.
        """
        for pattern in self._success_patterns:
            if pattern.search(content):
                return True
        return False

    def _detect_bot_loop(self, history: list[Message]) -> bool:
        """Detect if the AI is stuck in a loop (same response repeated).

        Args:
            history: Conversation history.

        Returns:
            True if bot loop detected.
        """
        ai_responses = [
            msg.content for msg in history
            if msg.speaker == MessageSpeaker.AI
        ]

        if len(ai_responses) < 2:
            return False

        # Check last 3 AI responses for repetition
        recent_responses = ai_responses[-3:]
        if len(recent_responses) >= 2:
            # If the last 2 AI responses are very similar
            for i in range(len(recent_responses) - 1):
                if self._calculate_similarity(
                    recent_responses[i], recent_responses[i + 1]
                ) > 0.8:
                    return True

        return False

    def _count_consecutive_failures(
        self,
        current_message: Message,
        history: list[Message],
    ) -> tuple[int, str]:
        """Count consecutive failures in conversation history.

        Failures are counted from most recent, resetting on success.

        Args:
            current_message: The current message being evaluated.
            history: Previous messages in the conversation.

        Returns:
            Tuple of (failure_count, reason_description).
        """
        if not history:
            return 0, "No history"

        # Combine history with current message for analysis
        all_messages = list(history)
        if current_message:
            all_messages.append(current_message)

        # Apply window limit
        if len(all_messages) > self._window * 2:
            all_messages = all_messages[-(self._window * 2):]

        failure_count = 0
        reasons = []

        # Get user messages for repetition detection
        user_messages = [
            msg for msg in all_messages
            if msg.speaker == MessageSpeaker.USER
        ]

        # Check for repeated questions (similarity)
        if len(user_messages) >= 2:
            repetition_count = 0
            for i in range(1, len(user_messages)):
                similarity = self._calculate_similarity(
                    user_messages[i].content,
                    user_messages[i - 1].content,
                )
                if similarity > 0.5:  # Threshold for "similar enough"
                    repetition_count += 1

            if repetition_count >= 2:
                failure_count = max(failure_count, repetition_count)
                reasons.append(f"User repeated similar question {repetition_count} times")

        # Scan through history for failures and successes
        consecutive_failures = 0
        for i, msg in enumerate(all_messages):
            if msg.speaker == MessageSpeaker.USER:
                # Check for user frustration
                if self._is_user_frustration(msg.content):
                    consecutive_failures += 1
                    reasons.append(f"User frustration: '{msg.content[:30]}...'")
                # Check for success (resets counter)
                elif self._is_success_indicator(msg.content):
                    consecutive_failures = 0
                    reasons = []

            elif msg.speaker == MessageSpeaker.AI:
                # Check for AI failure response
                if self._is_ai_failure(msg.content):
                    consecutive_failures += 1
                    reasons.append(f"AI failure: '{msg.content[:30]}...'")

        # Check for bot loop
        if self._detect_bot_loop(all_messages):
            consecutive_failures += 1
            reasons.append("Bot loop detected")

        # Take the maximum of repetition-based and sequential failures
        failure_count = max(failure_count, consecutive_failures)

        reason_str = "; ".join(reasons[-3:]) if reasons else "No failures detected"
        return failure_count, reason_str

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate conversation history for failure patterns.

        Args:
            message: The current message to evaluate.
            history: Previous messages in the conversation.
            context: Additional context for evaluation.

        Returns:
            TriggerResult indicating if failure threshold was reached.
        """
        start_time = time.perf_counter()

        # Log evaluation start
        message_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
        self._logger.debug(
            "Evaluating failure tracking trigger",
            extra={
                "message_preview": message_preview,
                "trigger_type": "failure_tracking",
                "threshold": self._threshold,
            },
        )

        # Handle no history case
        if not history:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._logger.debug(
                "Failure tracking trigger - no history",
                extra={
                    "triggered": False,
                    "confidence": 0.0,
                    "duration_ms": round(duration_ms, 2),
                    "trigger_type": "failure_tracking",
                },
            )
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                reason="No conversation history to analyze",
                metadata={"duration_ms": round(duration_ms, 2)},
            )

        # Count consecutive failures
        failure_count, reason = self._count_consecutive_failures(message, history)

        # Log failure count
        self._logger.debug(
            "Failure tracking trigger - analysis complete",
            extra={
                "failure_count": failure_count,
                "threshold": self._threshold,
                "trigger_type": "failure_tracking",
            },
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Check if threshold reached
        if failure_count >= self._threshold:
            # Calculate confidence based on how far over threshold
            confidence = min(0.9, 0.8 + (failure_count - self._threshold) * 0.05)

            self._logger.debug(
                "Failure tracking trigger - triggered",
                extra={
                    "triggered": True,
                    "confidence": confidence,
                    "failure_count": failure_count,
                    "reason": reason,
                    "duration_ms": round(duration_ms, 2),
                    "trigger_type": "failure_tracking",
                },
            )

            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.FAILURE_PATTERN,
                confidence=confidence,
                reason=f"Failure threshold reached ({failure_count}/{self._threshold}): {reason}",
                metadata={
                    "duration_ms": round(duration_ms, 2),
                    "failure_count": failure_count,
                    "threshold": self._threshold,
                },
            )

        # Below threshold
        self._logger.debug(
            "Failure tracking trigger - below threshold",
            extra={
                "triggered": False,
                "failure_count": failure_count,
                "threshold": self._threshold,
                "duration_ms": round(duration_ms, 2),
                "trigger_type": "failure_tracking",
            },
        )

        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            reason=f"Below failure threshold ({failure_count}/{self._threshold})",
            metadata={
                "duration_ms": round(duration_ms, 2),
                "failure_count": failure_count,
                "threshold": self._threshold,
            },
        )
