"""Test HandoffOrchestrator integration with ConversationPackager."""

from datetime import datetime, timezone

from handoffkit import HandoffOrchestrator, Message


def test_orchestrator_packages_conversation_in_handoff():
    """Test that HandoffOrchestrator packages conversation history in handoff."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="I need help with my account",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Message(
            speaker="ai",
            content="I'd be happy to help",
            timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
        ),
    ]

    result = orchestrator.create_handoff(messages, metadata={"user_id": "123"})

    # Verify conversation_package is in metadata
    assert "conversation_package" in result.metadata
    package = result.metadata["conversation_package"]

    # Verify package structure
    assert package["message_count"] == 2
    assert package["total_messages"] == 2
    assert package["truncated"] is False
    assert package["size_bytes"] > 0

    # Verify messages are formatted correctly
    assert len(package["messages"]) == 2
    assert package["messages"][0]["speaker"] == "user"
    assert package["messages"][0]["content"] == "I need help with my account"
    assert package["messages"][1]["speaker"] == "ai"


def test_orchestrator_limits_conversation_package():
    """Test that HandoffOrchestrator respects message limits."""
    # Create orchestrator with custom max_messages=5
    from handoffkit import HandoffConfig

    config = HandoffConfig(max_context_messages=5)
    orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

    # Create 10 messages
    messages = [
        Message(
            speaker="user",
            content=f"Message {i}",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        for i in range(10)
    ]

    result = orchestrator.create_handoff(messages)

    package = result.metadata["conversation_package"]

    # Should only include most recent 5 messages
    assert package["message_count"] == 5
    assert package["total_messages"] == 10
    assert package["truncated"] is True

    # Verify most recent messages are kept
    assert package["messages"][0]["content"] == "Message 5"
    assert package["messages"][-1]["content"] == "Message 9"
