"""Metadata collection for handoff context."""

import uuid

from handoffkit.context.models import ConversationMetadata
from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.utils.logging import get_logger


class MetadataCollector:
    """Collect conversation metadata for handoff context.

    This class extracts and analyzes metadata from conversations to provide
    rich context for human agents receiving handoffs.

    Example:
        >>> collector = MetadataCollector()
        >>> metadata = collector.collect_metadata(messages, {"user_id": "123"})
        >>> metadata.user_id
        '123'
    """

    def __init__(self) -> None:
        """Initialize metadata collector.

        Example:
            >>> collector = MetadataCollector()
        """
        self._logger = get_logger("context.metadata")

    def collect_metadata(
        self,
        conversation: list[Message],
        provided_metadata: dict,
    ) -> ConversationMetadata:
        """Collect comprehensive metadata from conversation and provided data.

        Args:
            conversation: List of Message objects from the conversation
            provided_metadata: User-provided metadata dictionary

        Returns:
            ConversationMetadata with all fields populated

        Example:
            >>> messages = [Message(speaker="user", content="Hello")]
            >>> metadata = collector.collect_metadata(messages, {"user_id": "123"})
            >>> metadata.user_id
            '123'
        """
        # Log metadata collection start
        self._logger.info(
            "Starting metadata collection",
            extra={
                "conversation_length": len(conversation),
                "provided_fields": list(provided_metadata.keys()),
            },
        )

        # Extract or generate core fields with warnings for missing required fields
        user_id = provided_metadata.get("user_id", "unknown")
        if user_id == "unknown":
            self._logger.warning(
                "Missing required field 'user_id', using default 'unknown'",
                extra={"field": "user_id"},
            )

        session_id = provided_metadata.get("session_id") or str(uuid.uuid4())
        if "session_id" not in provided_metadata or not provided_metadata.get("session_id"):
            self._logger.info(
                "Session ID not provided, auto-generating UUID",
                extra={"session_id": session_id},
            )

        channel = provided_metadata.get("channel", "unknown")

        # Extract conversation analytics
        attempted_solutions = self._extract_solutions(conversation)
        failed_queries = self._detect_failed_queries(conversation)
        duration = self._calculate_duration(conversation)

        result = ConversationMetadata(
            user_id=user_id,
            session_id=session_id,
            channel=channel,
            attempted_solutions=attempted_solutions,
            failed_queries=failed_queries,
            conversation_duration=duration,
            timestamp=conversation[-1].timestamp if conversation else None,
        )

        # Log metadata collection completion
        self._logger.info(
            "Metadata collection completed",
            extra={
                "user_id": result.user_id,
                "session_id": result.session_id,
                "channel": result.channel,
                "solutions_count": len(result.attempted_solutions),
                "failed_queries_count": len(result.failed_queries),
                "duration": result.conversation_duration,
            },
        )

        return result

    def _extract_solutions(self, conversation: list[Message]) -> list[str]:
        """Extract AI-provided solutions from conversation.

        Looks for AI messages containing solution-oriented language:
        - Instructions ("try", "you can", "please")
        - Solutions ("here's how", "solution")
        - Suggestions ("I recommend", "consider")

        Args:
            conversation: List of Message objects

        Returns:
            List of solution strings (last 5, truncated to 200 chars each)

        Example:
            >>> solutions = collector._extract_solutions(messages)
            >>> len(solutions) <= 5
            True
        """
        solutions = []
        solution_keywords = ["try", "you can", "here's how", "solution", "recommend"]

        for msg in conversation:
            if msg.speaker == MessageSpeaker.AI:
                # Check if message contains solution-oriented language
                content_lower = msg.content.lower()
                if any(keyword in content_lower for keyword in solution_keywords):
                    solutions.append(msg.content[:200])  # Truncate long messages

        return solutions[-5:]  # Last 5 solutions

    def _detect_failed_queries(self, conversation: list[Message]) -> list[str]:
        """Detect user questions that weren't answered satisfactorily.

        A query is considered failed if:
        - User asks a question (contains "?")
        - AI response seems uncertain or unable to help

        Args:
            conversation: List of Message objects

        Returns:
            List of failed query strings (last 5, truncated to 200 chars each)

        Example:
            >>> failed = collector._detect_failed_queries(messages)
            >>> isinstance(failed, list)
            True
        """
        failed = []

        for i, msg in enumerate(conversation):
            if msg.speaker == MessageSpeaker.USER and "?" in msg.content:
                # Check if next AI response seems uncertain
                if i + 1 < len(conversation):
                    next_msg = conversation[i + 1]
                    if next_msg.speaker == MessageSpeaker.AI:
                        # Simple heuristic: if AI says "I don't know", "I can't", etc.
                        uncertain_phrases = [
                            "i don't know",
                            "i can't",
                            "not sure",
                            "unable to",
                        ]
                        if any(
                            phrase in next_msg.content.lower()
                            for phrase in uncertain_phrases
                        ):
                            failed.append(msg.content[:200])

        return failed[-5:]  # Limit to last 5 failed queries

    def _calculate_duration(self, conversation: list[Message]) -> int:
        """Calculate conversation duration in seconds.

        Args:
            conversation: List of Message objects

        Returns:
            Duration from first to last message in seconds, or 0 if <2 messages

        Example:
            >>> duration = collector._calculate_duration(messages)
            >>> duration >= 0
            True
        """
        if len(conversation) < 2:
            return 0

        first_timestamp = conversation[0].timestamp
        last_timestamp = conversation[-1].timestamp

        # Defensive check for None timestamps (type safety)
        if first_timestamp is None or last_timestamp is None:
            return 0

        duration = (last_timestamp - first_timestamp).total_seconds()
        return int(duration)
