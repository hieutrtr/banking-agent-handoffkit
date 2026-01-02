"""Conversation summarization for handoff context."""

import time

from handoffkit.context.models import ConversationSummary
from handoffkit.core.types import Message, MessageSpeaker
from handoffkit.utils.logging import get_logger


class ConversationSummarizer:
    """Generate concise summaries of conversations for handoff context.

    This class analyzes conversations to extract key information and
    generate template-based summaries for human agents.

    Attributes:
        _max_words: Maximum word count for summary (default 200)
        _logger: Logger instance for structured logging

    Example:
        >>> summarizer = ConversationSummarizer(max_words=200)
        >>> summary = summarizer.summarize(messages)
        >>> summary.summary_text
        'Issue: Payment failed. Tried: Reset card. Status: Unresolved.'
    """

    def __init__(self, max_words: int = 200) -> None:
        """Initialize conversation summarizer.

        Args:
            max_words: Maximum word count for summary (default 200, minimum 1)

        Raises:
            ValueError: If max_words is less than 1

        Example:
            >>> summarizer = ConversationSummarizer()
            >>> summarizer = ConversationSummarizer(max_words=100)
        """
        if max_words < 1:
            raise ValueError(f"max_words must be at least 1, got {max_words}")
        self._max_words = max_words
        self._logger = get_logger("context.summarizer")

    def summarize(self, conversation: list[Message]) -> ConversationSummary:
        """Generate summary of conversation.

        Analyzes the conversation to extract the primary issue, attempted
        solutions, and current status, then generates a template-based summary.

        Args:
            conversation: List of Message objects from the conversation

        Returns:
            ConversationSummary with issue, solutions, status, and formatted text

        Example:
            >>> messages = [Message(speaker=MessageSpeaker.USER, content="Help")]
            >>> summary = summarizer.summarize(messages)
            >>> summary.current_status
            'unresolved'
        """
        start_time = time.perf_counter()

        self._logger.info(
            "Starting conversation summarization",
            extra={"conversation_length": len(conversation)},
        )

        issue = self._extract_issue(conversation)
        solutions = self._extract_solutions(conversation)
        status = self._detect_status(conversation)

        summary_text = self._generate_template_summary(issue, solutions, status)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        result = ConversationSummary(
            summary_text=summary_text,
            issue=issue,
            attempted_solutions=solutions,
            current_status=status,
            word_count=len(summary_text.split()),
            generation_time_ms=elapsed_ms,
        )

        self._logger.info(
            "Conversation summarization completed",
            extra={
                "word_count": result.word_count,
                "status": result.current_status,
                "solutions_count": len(result.attempted_solutions),
                "generation_time_ms": round(result.generation_time_ms, 2),
            },
        )

        return result

    def _extract_issue(self, conversation: list[Message]) -> str:
        """Extract primary issue from conversation.

        Looks for user messages containing problem indicators like
        "help with", "issue with", "problem", "can't", "won't".
        Falls back to first user message if no indicators found.

        Args:
            conversation: List of Message objects

        Returns:
            Issue description string (max 50 words)

        Example:
            >>> issue = summarizer._extract_issue(messages)
            >>> len(issue.split()) <= 50
            True
        """
        problem_indicators = [
            "help with",
            "issue with",
            "problem",
            "can't",
            "won't",
            "unable to",
            "need to",
        ]

        # First pass: look for messages with problem indicators
        for msg in conversation:
            if msg.speaker == MessageSpeaker.USER:
                content_lower = msg.content.lower()
                if any(indicator in content_lower for indicator in problem_indicators):
                    return self._truncate_to_words(msg.content, 50)

        # Fallback: use first user message
        for msg in conversation:
            if msg.speaker == MessageSpeaker.USER:
                return self._truncate_to_words(msg.content, 50)

        return "No issue identified"

    def _extract_solutions(self, conversation: list[Message]) -> list[str]:
        """Extract attempted solutions from AI responses.

        Looks for AI messages containing solution-oriented language like
        "try", "you can", "here's how", "solution", "recommend".

        Args:
            conversation: List of Message objects

        Returns:
            List of solution strings (max 3, truncated to 30 words each)

        Example:
            >>> solutions = summarizer._extract_solutions(messages)
            >>> len(solutions) <= 3
            True
        """
        solutions = []
        solution_keywords = ["try", "you can", "here's how", "solution", "recommend"]

        for msg in conversation:
            if msg.speaker == MessageSpeaker.AI:
                content_lower = msg.content.lower()
                if any(keyword in content_lower for keyword in solution_keywords):
                    solutions.append(self._truncate_to_words(msg.content, 30))

        return solutions[-3:]  # Last 3 solutions (more concise than metadata's 5)

    def _detect_status(self, conversation: list[Message]) -> str:
        """Detect current conversation status.

        Analyzes the last 2-3 messages to determine if the conversation is:
        - resolved: User expressed satisfaction or thanks
        - unresolved: User still has issues or questions
        - awaiting_response: AI asked a question, waiting for user

        Args:
            conversation: List of Message objects

        Returns:
            Status string: "resolved", "unresolved", or "awaiting_response"

        Example:
            >>> status = summarizer._detect_status(messages)
            >>> status in ["resolved", "unresolved", "awaiting_response", "unknown"]
            True
        """
        if not conversation:
            return "unknown"

        # Check awaiting_response first - if last message is AI asking a question
        # and there's no user response after it, status is awaiting response
        if conversation[-1].speaker == MessageSpeaker.AI:
            if "?" in conversation[-1].content:
                return "awaiting_response"

        # Analyze last 2-3 messages for status indicators
        recent = conversation[-3:] if len(conversation) >= 3 else conversation

        resolved_indicators = [
            "thank",
            "thanks",
            "perfect",
            "that worked",
            "solved",
            "resolved",
        ]
        unresolved_indicators = ["still", "doesn't work", "not working", "help", "?"]

        # Find last user message in recent messages
        for msg in reversed(recent):
            if msg.speaker == MessageSpeaker.USER:
                content_lower = msg.content.lower()
                if any(ind in content_lower for ind in resolved_indicators):
                    return "resolved"
                if any(ind in content_lower for ind in unresolved_indicators):
                    return "unresolved"
                break  # Only check the last user message

        return "unresolved"  # Default to unresolved for handoff

    def _generate_template_summary(
        self, issue: str, solutions: list[str], status: str
    ) -> str:
        """Generate template-based summary with proportional truncation.

        Creates a summary in the format:
        "Issue: {issue}. Tried: {solutions}. Status: {status}."

        When truncation is needed, applies proportional truncation that
        preserves the ratio between Issue and Tried sections while keeping
        Status intact.

        Args:
            issue: Primary issue description
            solutions: List of attempted solutions
            status: Current conversation status

        Returns:
            Formatted summary text (max max_words)

        Example:
            >>> text = summarizer._generate_template_summary("Payment", ["Reset"], "unresolved")
            >>> "Issue:" in text and "Status:" in text
            True
        """
        # Build status part first (fixed, never truncated)
        status_map = {
            "resolved": "Resolved",
            "unresolved": "Unresolved - needs human assistance",
            "awaiting_response": "Awaiting customer response",
            "unknown": "Status unknown",
        }
        status_text = f"Status: {status_map.get(status, status)}"
        status_words = len(status_text.split())

        # Build solutions part
        if solutions:
            solutions_text = "; ".join(solutions[:3])
            tried_text = f"Tried: {solutions_text}"
        else:
            tried_text = "Tried: No solutions attempted"

        issue_text = f"Issue: {issue}"

        # Calculate word counts
        issue_words = len(issue_text.split())
        tried_words = len(tried_text.split())
        total_words = issue_words + tried_words + status_words

        # Check if truncation needed
        if total_words <= self._max_words:
            summary = f"{issue_text} {tried_text} {status_text}"
        else:
            # Proportional truncation: preserve status, truncate issue and tried proportionally
            available_words = self._max_words - status_words
            if available_words < 2:
                # Extreme case: just return status
                summary = status_text
            else:
                # Calculate proportional allocation
                content_total = issue_words + tried_words
                issue_ratio = issue_words / content_total if content_total > 0 else 0.5
                tried_ratio = tried_words / content_total if content_total > 0 else 0.5

                # Allocate words proportionally (minimum 1 word each)
                issue_budget = max(1, int(available_words * issue_ratio))
                tried_budget = max(1, available_words - issue_budget)

                # Truncate each part
                issue_text = self._truncate_to_words(issue, issue_budget - 1)  # -1 for "Issue:"
                issue_text = f"Issue: {issue_text}"

                if solutions:
                    solutions_text = "; ".join(solutions[:3])
                    solutions_text = self._truncate_to_words(solutions_text, tried_budget - 1)  # -1 for "Tried:"
                    tried_text = f"Tried: {solutions_text}"
                else:
                    tried_text = self._truncate_to_words("No solutions attempted", tried_budget - 1)
                    tried_text = f"Tried: {tried_text}"

                summary = f"{issue_text} {tried_text} {status_text}"

        return summary

    def _truncate_to_words(self, text: str, max_words: int) -> str:
        """Truncate text to specified word count.

        Args:
            text: Text to truncate
            max_words: Maximum word count

        Returns:
            Truncated text with "..." suffix if truncated

        Example:
            >>> summarizer._truncate_to_words("one two three", 2)
            'one two...'
        """
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return text
