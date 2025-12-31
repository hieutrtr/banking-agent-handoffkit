"""Tests for ConversationPackager class."""

import json
import time
from datetime import datetime, timezone

import pytest

from handoffkit.context.packager import ConversationPackager
from handoffkit.context.models import ConversationPackage
from handoffkit.core.types import Message, MessageSpeaker


class TestConversationPackager:
    """Test suite for ConversationPackager."""

    def test_package_empty_conversation(self):
        """Test packaging an empty conversation."""
        packager = ConversationPackager()
        result = packager.package_conversation([])

        assert isinstance(result, ConversationPackage)
        assert result.messages == []
        assert result.message_count == 0
        assert result.total_messages == 0
        assert result.truncated is False
        assert result.size_bytes == 0

    def test_package_10_messages(self):
        """Test packaging exactly 10 messages with all fields."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"User message {i}",
                timestamp=datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc),
                metadata={"ai_confidence": 0.95 if i % 2 == 0 else None},
            )
            for i in range(10)
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        assert result.message_count == 10
        assert result.total_messages == 10
        assert result.truncated is False
        assert len(result.messages) == 10

        # Validate first message format
        msg = result.messages[0]
        assert msg["speaker"] == "user"
        assert msg["content"] == "User message 0"
        assert msg["timestamp"] == "2024-01-01T12:00:00+00:00"
        assert msg["ai_confidence"] == 0.95

    def test_message_count_limiting_to_100(self):
        """Test that messages are limited to most recent 100."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"Message {i}",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
            for i in range(150)
        ]

        packager = ConversationPackager(max_messages=100)
        result = packager.package_conversation(messages)

        assert result.message_count == 100
        assert result.total_messages == 150
        assert result.truncated is True
        # Most recent messages should be kept
        assert result.messages[0]["content"] == "Message 50"
        assert result.messages[-1]["content"] == "Message 149"

    def test_size_capping_at_50kb(self):
        """Test that total size is capped at 50KB."""
        # Create messages that will exceed 50KB
        large_content = "x" * 2000  # 2KB per message
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=large_content,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
            for _ in range(50)  # 50 messages * 2KB = 100KB
        ]

        packager = ConversationPackager(max_messages=100, max_size_kb=50)
        result = packager.package_conversation(messages)

        assert result.size_bytes <= 50 * 1024
        assert result.truncated is True
        assert result.message_count < 50  # Should have removed messages

    def test_json_serialization_validity(self):
        """Test that packaged result is valid JSON."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Test message",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                metadata={"ai_confidence": 0.9},
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        # to_json() should produce valid JSON
        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert parsed["message_count"] == 1
        assert parsed["messages"][0]["content"] == "Test message"

    def test_from_json_roundtrip(self):
        """Test ConversationPackage.from_json() reconstruction."""
        messages = [
            Message(
                speaker=MessageSpeaker.AI,
                content="AI response",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
        ]

        packager = ConversationPackager()
        original = packager.package_conversation(messages)
        json_str = original.to_json()

        # Reconstruct from JSON
        reconstructed = ConversationPackage.from_json(json_str)

        assert reconstructed.message_count == original.message_count
        assert reconstructed.total_messages == original.total_messages
        assert reconstructed.truncated == original.truncated
        assert reconstructed.size_bytes == original.size_bytes
        assert reconstructed.messages == original.messages

    def test_ai_confidence_metadata_included(self):
        """Test AI confidence is included when present in metadata."""
        messages = [
            Message(
                speaker=MessageSpeaker.AI,
                content="Response",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                metadata={"ai_confidence": 0.87},
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        assert result.messages[0]["ai_confidence"] == 0.87

    def test_ai_confidence_none_when_missing(self):
        """Test AI confidence is None when not in metadata."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="User message",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                metadata={},
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        assert result.messages[0]["ai_confidence"] is None

    def test_single_message_conversation(self):
        """Test edge case: single message."""
        messages = [
            Message(
                speaker=MessageSpeaker.SYSTEM,
                content="System message",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        assert result.message_count == 1
        assert result.total_messages == 1
        assert result.truncated is False
        assert result.messages[0]["speaker"] == "system"

    def test_very_long_single_message(self):
        """Test edge case: single message exceeding size limit."""
        # Create a message that exceeds 50KB by itself
        large_content = "x" * 60000  # 60KB
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=large_content,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
        ]

        packager = ConversationPackager(max_size_kb=50)
        result = packager.package_conversation(messages)

        # Should still include the message (can't remove last message)
        assert result.message_count == 1
        # But it will exceed the size limit
        assert result.size_bytes > 50 * 1024

    def test_speaker_enum_to_string_conversion(self):
        """Test that MessageSpeaker enums are converted to strings."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="User",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.AI,
                content="AI",
                timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
            ),
            Message(
                speaker=MessageSpeaker.SYSTEM,
                content="System",
                timestamp=datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc),
            ),
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        assert result.messages[0]["speaker"] == "user"
        assert result.messages[1]["speaker"] == "ai"
        assert result.messages[2]["speaker"] == "system"

    def test_timestamp_iso8601_format(self):
        """Test that timestamps are formatted as ISO 8601."""
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Test",
                timestamp=datetime(2024, 12, 25, 15, 30, 45, 123456, tzinfo=timezone.utc),
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        # ISO 8601 format with microseconds
        assert result.messages[0]["timestamp"] == "2024-12-25T15:30:45.123456+00:00"

    def test_size_calculation_uses_utf8(self):
        """Test that size calculation uses UTF-8 encoding."""
        # UTF-8 characters take multiple bytes
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content="Hello 世界 🌍",  # Mix of ASCII, Chinese, emoji
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
        ]

        packager = ConversationPackager()
        result = packager.package_conversation(messages)

        # Verify size is calculated correctly
        json_str = json.dumps(result.messages)
        expected_size = len(json_str.encode("utf-8"))
        assert result.size_bytes == expected_size

    def test_performance_under_50ms(self):
        """Test that packaging 100 messages completes in under 50ms.

        Requirement: Performance Requirements specify <50ms for packaging.
        """
        messages = [
            Message(
                speaker=MessageSpeaker.USER,
                content=f"This is message number {i} with reasonable content length",
                timestamp=datetime(2024, 1, 1, 12, i % 60, 0, tzinfo=timezone.utc),
                metadata={"ai_confidence": 0.85},
            )
            for i in range(100)
        ]

        packager = ConversationPackager()

        start_time = time.perf_counter()
        _ = packager.package_conversation(messages)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 50, f"Packaging took {elapsed_ms:.2f}ms, expected <50ms"

    def test_invalid_max_messages_zero(self):
        """Test that max_messages=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_messages must be a positive integer"):
            ConversationPackager(max_messages=0)

    def test_invalid_max_messages_negative(self):
        """Test that negative max_messages raises ValueError."""
        with pytest.raises(ValueError, match="max_messages must be a positive integer"):
            ConversationPackager(max_messages=-5)

    def test_invalid_max_messages_float(self):
        """Test that float max_messages raises ValueError."""
        with pytest.raises(ValueError, match="max_messages must be a positive integer"):
            ConversationPackager(max_messages=10.5)

    def test_invalid_max_size_kb_zero(self):
        """Test that max_size_kb=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_size_kb must be a positive integer"):
            ConversationPackager(max_size_kb=0)

    def test_invalid_max_size_kb_negative(self):
        """Test that negative max_size_kb raises ValueError."""
        with pytest.raises(ValueError, match="max_size_kb must be a positive integer"):
            ConversationPackager(max_size_kb=-10)

    def test_invalid_max_size_kb_float(self):
        """Test that float max_size_kb raises ValueError."""
        with pytest.raises(ValueError, match="max_size_kb must be a positive integer"):
            ConversationPackager(max_size_kb=25.5)
