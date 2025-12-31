"""Tests for MetadataCollector class."""

import uuid
from datetime import datetime, timezone

import pytest

from handoffkit.context.metadata import MetadataCollector
from handoffkit.context.models import ConversationMetadata
from handoffkit.core.types import Message, MessageSpeaker


class TestMetadataCollector:
    """Test MetadataCollector functionality."""

    def test_full_metadata_collection_with_all_fields(self):
        """Test metadata collection with all fields provided."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help with my account",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="I'd be happy to help. You can try resetting your password",
                timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {
            "user_id": "user123",
            "session_id": "session456",
            "channel": "web",
        }

        result = collector.collect_metadata(messages, provided_metadata)

        assert result.user_id == "user123"
        assert result.session_id == "session456"
        assert result.channel == "web"
        assert result.conversation_duration == 30
        assert result.timestamp == messages[-1].timestamp

    def test_session_id_auto_generation(self):
        """Test that session_id is auto-generated when not provided."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Verify session_id is a valid UUID v4
        assert result.session_id is not None
        uuid_obj = uuid.UUID(result.session_id, version=4)
        assert str(uuid_obj) == result.session_id

    def test_default_values_for_missing_fields(self):
        """Test that missing fields get default values."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {}  # No fields provided

        result = collector.collect_metadata(messages, provided_metadata)

        assert result.user_id == "unknown"
        assert result.channel == "unknown"
        assert result.session_id is not None  # Auto-generated
        assert result.attempted_solutions == []
        assert result.failed_queries == []

    def test_attempted_solutions_extraction(self):
        """Test extraction of AI solutions from conversation."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="How do I reset my password?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="You can try resetting your password by clicking the forgot password link",
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

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Should extract AI messages with solution keywords
        assert len(result.attempted_solutions) == 2
        assert "try" in result.attempted_solutions[0].lower()
        assert "recommend" in result.attempted_solutions[1].lower()

    def test_attempted_solutions_limit_to_five(self):
        """Test that attempted_solutions is limited to last 5."""
        collector = MetadataCollector()

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

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Should only have last 5 solutions
        assert len(result.attempted_solutions) == 5
        assert "solution 9" in result.attempted_solutions[-1]

    def test_failed_queries_detection(self):
        """Test detection of failed queries."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Can you help me with billing?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="I don't know about billing issues",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.USER,
                content="What about refunds?",
                timestamp=datetime(2024, 1, 1, 12, 0, 20, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="I can't help with refund requests",
                timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Should detect both failed queries
        assert len(result.failed_queries) == 2
        assert "billing" in result.failed_queries[0].lower()
        assert "refunds" in result.failed_queries[1].lower()

    def test_conversation_duration_calculation(self):
        """Test conversation duration calculation."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Hi there!",
                timestamp=datetime(2024, 1, 1, 12, 5, 30, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Duration should be 5 minutes 30 seconds = 330 seconds
        assert result.conversation_duration == 330

    def test_empty_conversation(self):
        """Test metadata collection with empty conversation."""
        collector = MetadataCollector()

        messages = []
        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        assert result.user_id == "user123"
        assert result.conversation_duration == 0
        assert result.timestamp is None
        assert result.attempted_solutions == []
        assert result.failed_queries == []

    def test_single_message_conversation(self):
        """Test conversation duration with single message."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Single message should have duration of 0
        assert result.conversation_duration == 0
        assert result.timestamp == messages[0].timestamp

    def test_conversation_with_no_solutions(self):
        """Test conversation with no AI solutions."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Hello there",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # No solution keywords in AI response
        assert result.attempted_solutions == []

    def test_conversation_with_no_failed_queries(self):
        """Test conversation with no failed queries."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Can you help me?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="Of course! Here's how to get started",
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # AI response is confident, not uncertain
        assert result.failed_queries == []

    def test_solution_truncation_to_200_chars(self):
        """Test that long solution messages are truncated."""
        collector = MetadataCollector()

        long_message = "You can try " + "a" * 500

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Help please",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content=long_message,
                timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
            ),
        ]

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        assert len(result.attempted_solutions) == 1
        assert len(result.attempted_solutions[0]) <= 200


class TestConversationMetadata:
    """Test ConversationMetadata model."""

    def test_conversation_metadata_to_dict(self):
        """Test ConversationMetadata serialization to dict."""
        metadata = ConversationMetadata(
            user_id="user123",
            session_id="session456",
            channel="web",
            attempted_solutions=["Try this", "Try that"],
            failed_queries=["What about X?"],
            conversation_duration=120,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = metadata.to_dict()

        assert result["user_id"] == "user123"
        assert result["session_id"] == "session456"
        assert result["channel"] == "web"
        assert result["attempted_solutions"] == ["Try this", "Try that"]
        assert result["failed_queries"] == ["What about X?"]
        assert result["conversation_duration"] == 120
        assert "timestamp" in result

    def test_conversation_metadata_defaults(self):
        """Test ConversationMetadata with default values."""
        metadata = ConversationMetadata(
            user_id="user123",
            session_id="session456",
            channel="web",
        )

        assert metadata.attempted_solutions == []
        assert metadata.failed_queries == []
        assert metadata.conversation_duration == 0
        assert metadata.timestamp is None


class TestMetadataCollectorEdgeCases:
    """Test edge cases for MetadataCollector."""

    def test_empty_string_session_id_auto_generates(self):
        """Test that empty string session_id triggers auto-generation."""
        collector = MetadataCollector()

        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        # Empty string should trigger auto-generation
        provided_metadata = {"user_id": "user123", "session_id": ""}

        result = collector.collect_metadata(messages, provided_metadata)

        # Should have auto-generated a valid UUID, not empty string
        assert result.session_id != ""
        uuid_obj = uuid.UUID(result.session_id, version=4)
        assert str(uuid_obj) == result.session_id

    def test_failed_queries_limit_to_five(self):
        """Test that failed_queries is limited to last 5."""
        collector = MetadataCollector()

        messages = []
        for i in range(10):
            messages.append(
                Message(
                    speaker=MessageSpeaker.USER,
                    content=f"Question {i}?",
                    timestamp=datetime(2024, 1, 1, 12, 0, i * 2, tzinfo=timezone.utc),
                )
            )
            messages.append(
                Message(
                    speaker=MessageSpeaker.AI,
                    content=f"I don't know about question {i}",
                    timestamp=datetime(2024, 1, 1, 12, 0, i * 2 + 1, tzinfo=timezone.utc),
                )
            )

        provided_metadata = {"user_id": "user123"}

        result = collector.collect_metadata(messages, provided_metadata)

        # Should only have last 5 failed queries
        assert len(result.failed_queries) == 5
        assert "Question 9" in result.failed_queries[-1]
