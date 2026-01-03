"""Test HandoffOrchestrator integration with ConversationPackager."""

from datetime import datetime, timezone

import pytest

from handoffkit import HandoffOrchestrator, Message


@pytest.mark.asyncio
async def test_orchestrator_packages_conversation_in_handoff():
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

    result = await orchestrator.create_handoff(messages, metadata={"user_id": "123"})

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


@pytest.mark.asyncio
async def test_orchestrator_limits_conversation_package():
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

    result = await orchestrator.create_handoff(messages)

    package = result.metadata["conversation_package"]

    # Should only include most recent 5 messages
    assert package["message_count"] == 5
    assert package["total_messages"] == 10
    assert package["truncated"] is True

    # Verify most recent messages are kept
    assert package["messages"][0]["content"] == "Message 5"
    assert package["messages"][-1]["content"] == "Message 9"


@pytest.mark.asyncio
async def test_orchestrator_generates_conversation_summary():
    """Test that HandoffOrchestrator generates conversation summary in handoff."""
    orchestrator = HandoffOrchestrator(helpdesk="zendesk")

    messages = [
        Message(
            speaker="user",
            content="I have a problem with my payment",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Message(
            speaker="ai",
            content="You can try refreshing your payment method",
            timestamp=datetime(2024, 1, 1, 12, 0, 10, tzinfo=timezone.utc),
        ),
        Message(
            speaker="user",
            content="It's still not working",
            timestamp=datetime(2024, 1, 1, 12, 0, 20, tzinfo=timezone.utc),
        ),
    ]

    result = await orchestrator.create_handoff(messages, metadata={"user_id": "123"})

    # Verify conversation_summary is in metadata
    assert "conversation_summary" in result.metadata
    summary = result.metadata["conversation_summary"]

    # Verify summary structure
    assert "summary_text" in summary
    assert "issue" in summary
    assert "attempted_solutions" in summary
    assert "current_status" in summary
    assert "word_count" in summary
    assert "generation_time_ms" in summary

    # Verify content
    assert "Issue:" in summary["summary_text"]
    assert summary["current_status"] == "unresolved"
    assert len(summary["attempted_solutions"]) == 1
    assert summary["word_count"] > 0
    assert summary["generation_time_ms"] > 0


@pytest.mark.asyncio
async def test_orchestrator_respects_summary_max_words():
    """Test that HandoffOrchestrator respects summary_max_words config."""
    from handoffkit import HandoffConfig

    config = HandoffConfig(summary_max_words=50)  # Minimum allowed value
    orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

    messages = [
        Message(
            speaker="user",
            content="I have a very long and detailed problem with my account that requires a lot of explanation " * 5,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    result = await orchestrator.create_handoff(messages)

    summary = result.metadata["conversation_summary"]

    # Summary should respect max_words
    assert summary["word_count"] <= 51  # 50 + potential "..."
