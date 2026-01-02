"""Tests for ConversationSummarizer class."""

import time
from datetime import datetime, timezone

import pytest

from handoffkit.context.models import ConversationSummary
from handoffkit.context.summarizer import ConversationSummarizer
from handoffkit.core.types import Message, MessageSpeaker


class TestConversationSummarizer:
    """Test ConversationSummarizer functionality."""

    def test_basic_summarization(self):
        """Test basic conversation summarization."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help with my payment issue",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="You can try refreshing your payment method",
                timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert isinstance(result, ConversationSummary)
        assert "Issue:" in result.summary_text
        assert "Tried:" in result.summary_text
        assert "Status:" in result.summary_text
        assert result.word_count > 0
        assert result.generation_time_ms > 0

    def test_issue_extraction_with_problem_indicators(self):
        """Test issue extraction from messages with problem indicators."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello there",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="I can't login to my account",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Should extract the message with "can't" indicator
        assert "login" in result.issue.lower() or "account" in result.issue.lower()

    def test_issue_extraction_fallback_to_first_user_message(self):
        """Test fallback to first user message when no problem indicators."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I want to change my email address",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert "email" in result.issue.lower() or "change" in result.issue.lower()

    def test_issue_truncation_to_50_words(self):
        """Test that long issues are truncated to 50 words."""
        summarizer = ConversationSummarizer()

        long_message = "I have a problem with " + " ".join(["word"] * 100)

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=long_message,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Issue should be truncated to ~50 words plus "..."
        assert len(result.issue.split()) <= 51  # 50 words + "..."
        assert result.issue.endswith("...")

    def test_solutions_extraction(self):
        """Test extraction of solutions from AI messages."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="How do I reset my password?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="You can try resetting your password via email",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="That didn't work",
                timestamp=datetime(2024, 1, 1, 12, 0, 20, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="I recommend contacting support directly",
                timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert len(result.attempted_solutions) == 2
        assert "try" in result.attempted_solutions[0].lower()
        assert "recommend" in result.attempted_solutions[1].lower()

    def test_solutions_limited_to_three(self):
        """Test that solutions are limited to last 3."""
        summarizer = ConversationSummarizer()

        messages = []
        for i in range(10):
            messages.append(
                Message(
                    speaker=MessageSpeaker.USER,
                    content=f"Question {i}",
                    timestamp=datetime(2024, 1, 1, 12, 0, i * 2, tzinfo=timezone.utc),
                )
            )
            messages.append(
                Message(
                    speaker=MessageSpeaker.AI,
                    content=f"You can try solution {i}",
                    timestamp=datetime(2024, 1, 1, 12, 0, i * 2 + 1, tzinfo=timezone.utc),
                )
            )

        result = summarizer.summarize(messages)

        # Should only have last 3 solutions
        assert len(result.attempted_solutions) == 3
        assert "solution 9" in result.attempted_solutions[-1]

    def test_solutions_truncated_to_30_words(self):
        """Test that each solution is truncated to 30 words."""
        summarizer = ConversationSummarizer()

        long_solution = "You can try " + " ".join(["word"] * 100)

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Help please",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content=long_solution,
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert len(result.attempted_solutions) == 1
        assert len(result.attempted_solutions[0].split()) <= 31  # 30 + "..."
        assert result.attempted_solutions[0].endswith("...")

    def test_status_detection_resolved(self):
        """Test detection of resolved status."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I have a problem",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Here's the solution",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="Thank you! That worked perfectly",
                timestamp=datetime(2024, 1, 1, 12, 0, 20, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.current_status == "resolved"

    def test_status_detection_unresolved(self):
        """Test detection of unresolved status."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I have a problem",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Try this solution",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="It's still not working, help!",
                timestamp=datetime(2024, 1, 1, 12, 0, 20, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.current_status == "unresolved"

    def test_status_detection_awaiting_response(self):
        """Test detection of awaiting_response status."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Can you tell me more about your issue?",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.current_status == "awaiting_response"

    def test_template_format(self):
        """Test template-based summary format."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I have a payment problem",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="You can try updating your card",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Template format: "Issue: X. Tried: Y. Status: Z."
        assert result.summary_text.startswith("Issue:")
        assert "Tried:" in result.summary_text
        assert "Status:" in result.summary_text

    def test_max_words_enforcement(self):
        """Test that summary respects max_words limit."""
        summarizer = ConversationSummarizer(max_words=20)

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I have a very long and detailed problem that spans many many words about my account",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.word_count <= 21  # 20 + "..."

    def test_empty_conversation(self):
        """Test summarization of empty conversation."""
        summarizer = ConversationSummarizer()

        messages = []

        result = summarizer.summarize(messages)

        assert result.issue == "No issue identified"
        assert result.attempted_solutions == []
        assert result.current_status == "unknown"
        assert result.word_count > 0

    def test_single_message_conversation(self):
        """Test summarization of single message conversation."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help with my account",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert "account" in result.issue.lower() or "help" in result.issue.lower()
        assert result.attempted_solutions == []
        assert result.current_status == "unresolved"

    def test_no_solutions_in_conversation(self):
        """Test conversation with no AI solutions."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Hello! How are you?",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.attempted_solutions == []
        assert "No solutions attempted" in result.summary_text

    def test_all_system_messages(self):
        """Test conversation with only SYSTEM messages."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.SYSTEM,
                content="System message 1",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.SYSTEM,
                content="System message 2",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.issue == "No issue identified"
        assert result.attempted_solutions == []


class TestConversationSummary:
    """Test ConversationSummary model."""

    def test_conversation_summary_to_dict(self):
        """Test ConversationSummary serialization to dict."""
        summary = ConversationSummary(
            summary_text="Issue: Test. Tried: Nothing. Status: Unknown.",
            issue="Test",
            attempted_solutions=["Try this", "Try that"],
            current_status="unresolved",
            word_count=10,
            generation_time_ms=5.2,
        )

        result = summary.to_dict()

        assert result["summary_text"] == "Issue: Test. Tried: Nothing. Status: Unknown."
        assert result["issue"] == "Test"
        assert result["attempted_solutions"] == ["Try this", "Try that"]
        assert result["current_status"] == "unresolved"
        assert result["word_count"] == 10
        assert result["generation_time_ms"] == 5.2

    def test_conversation_summary_defaults(self):
        """Test ConversationSummary with default values."""
        summary = ConversationSummary(
            summary_text="Issue: Test",
            issue="Test",
            current_status="unknown",
            word_count=2,
            generation_time_ms=1.0,
        )

        assert summary.attempted_solutions == []


class TestConversationSummarizerEdgeCases:
    """Test edge cases for ConversationSummarizer."""

    def test_multiple_problem_indicators_uses_first(self):
        """Test that first message with problem indicator is used."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I can't access my email",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="I also have a problem with billing",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Should use first message with problem indicator
        assert "email" in result.issue.lower()

    def test_status_with_question_mark_in_user_message(self):
        """Test status detection when user asks question."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Why isn't this working?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Question with "?" should be unresolved
        assert result.current_status == "unresolved"

    def test_custom_max_words(self):
        """Test custom max_words configuration."""
        summarizer = ConversationSummarizer(max_words=10)

        long_issue = "I have a very long problem description " * 10

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=long_issue,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Summary should respect max_words
        assert result.word_count <= 11  # 10 + potential "..."

    def test_performance_under_100ms(self):
        """Test that summarization completes in under 100ms.

        Requirement: Template-based summarization should be very fast.
        """
        summarizer = ConversationSummarizer()

        # Create realistic conversation with 100 messages (max limit)
        messages = []
        for i in range(100):
            messages.append(
                Message(
                    speaker=MessageSpeaker.USER if i % 2 == 0 else MessageSpeaker.AI,
                    content=f"This is message {i} with some reasonable content. You can try this solution. I have a problem with payment.",
                    timestamp=datetime(2024, 1, 1, 12 + (i // 60), i % 60, 0, tzinfo=timezone.utc),
                )
            )

        start_time = time.perf_counter()
        _ = summarizer.summarize(messages)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 100, f"Summarization took {elapsed_ms:.2f}ms, expected <100ms"

    def test_mixed_speaker_types(self):
        """Test conversation with mixed speaker types including SYSTEM."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.SYSTEM,
                content="You can try this system command",  # Has solution keyword
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="I have a problem with my order",
                timestamp=datetime(2024, 1, 1, 12, 0, 5, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="You can try checking your order status",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # SYSTEM message should not be in solutions (only AI)
        assert len(result.attempted_solutions) == 1
        assert "order status" in result.attempted_solutions[0].lower()
        # Issue should come from USER message
        assert "order" in result.issue.lower() or "problem" in result.issue.lower()

    def test_status_map_values(self):
        """Test all status map values in template."""
        summarizer = ConversationSummarizer()

        # Test resolved
        resolved_messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Thanks, that solved it!",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]
        result = summarizer.summarize(resolved_messages)
        assert "Resolved" in result.summary_text

        # Test unresolved
        unresolved_messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="It's still broken",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]
        result = summarizer.summarize(unresolved_messages)
        assert "Unresolved" in result.summary_text

        # Test awaiting response
        awaiting_messages = [
            Message(
                speaker=MessageSpeaker.AI,
                content="What is your account number?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]
        result = summarizer.summarize(awaiting_messages)
        assert "Awaiting" in result.summary_text

    def test_word_count_accuracy(self):
        """Test that word_count is accurate."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Help",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        actual_word_count = len(result.summary_text.split())
        assert result.word_count == actual_word_count

    def test_generation_time_tracked(self):
        """Test that generation time is tracked."""
        summarizer = ConversationSummarizer()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Test message",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        assert result.generation_time_ms > 0
        assert result.generation_time_ms < 1000  # Should be well under 1 second

    def test_max_words_zero_raises_error(self):
        """Test that max_words=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_words must be at least 1"):
            ConversationSummarizer(max_words=0)

    def test_max_words_negative_raises_error(self):
        """Test that negative max_words raises ValueError."""
        with pytest.raises(ValueError, match="max_words must be at least 1"):
            ConversationSummarizer(max_words=-5)

    def test_max_words_one_works(self):
        """Test that max_words=1 is valid boundary case."""
        summarizer = ConversationSummarizer(max_words=1)

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Help with my account",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = summarizer.summarize(messages)

        # Should work without crashing
        assert result.word_count >= 1
