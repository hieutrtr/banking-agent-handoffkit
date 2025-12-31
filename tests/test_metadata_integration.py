"""Integration tests for metadata collection with HandoffOrchestrator."""

from datetime import datetime, timezone

from handoffkit import HandoffOrchestrator, Message


def test_orchestrator_collects_metadata_in_handoff():
    """Test that HandoffOrchestrator collects conversation metadata."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="I need help with my account",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Message(
            speaker="ai",
            content="I'd be happy to help. You can try resetting your password",
            timestamp=datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc),
        ),
    ]

    result = orchestrator.create_handoff(messages, metadata={"user_id": "123"})

    # Verify conversation_metadata is in metadata
    assert "conversation_metadata" in result.metadata
    meta = result.metadata["conversation_metadata"]

    # Verify metadata structure
    assert meta["user_id"] == "123"
    assert "session_id" in meta  # Auto-generated
    assert meta["conversation_duration"] == 30
    assert len(meta["attempted_solutions"]) > 0  # Contains "try"


def test_orchestrator_auto_generates_session_id():
    """Test that session_id is auto-generated when not provided."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="Hello",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    result = orchestrator.create_handoff(messages, metadata={"user_id": "123"})

    meta = result.metadata["conversation_metadata"]

    # Verify session_id is present and is a valid UUID
    assert "session_id" in meta
    assert len(meta["session_id"]) > 0
    assert "-" in meta["session_id"]  # UUID format


def test_orchestrator_handles_empty_metadata():
    """Test metadata collection with no provided metadata."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="Hello",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    result = orchestrator.create_handoff(messages, metadata={})

    meta = result.metadata["conversation_metadata"]

    # Verify defaults are applied
    assert meta["user_id"] == "unknown"
    assert meta["channel"] == "unknown"
    assert "session_id" in meta
    assert meta["attempted_solutions"] == []
    assert meta["failed_queries"] == []


def test_orchestrator_includes_both_package_and_metadata():
    """Test that both conversation_package and conversation_metadata are included."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="Help me",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Message(
            speaker="ai",
            content="You can try this solution",
            timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
        ),
    ]

    result = orchestrator.create_handoff(
        messages, metadata={"user_id": "user456", "channel": "web"}
    )

    # Both should be present
    assert "conversation_package" in result.metadata
    assert "conversation_metadata" in result.metadata

    # Verify conversation_package
    package = result.metadata["conversation_package"]
    assert package["message_count"] == 2

    # Verify conversation_metadata
    meta = result.metadata["conversation_metadata"]
    assert meta["user_id"] == "user456"
    assert meta["channel"] == "web"
