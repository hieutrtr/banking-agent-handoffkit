"""Pytest configuration and fixtures for HandoffKit tests."""

import pytest

from handoffkit import HandoffConfig, HandoffOrchestrator
from handoffkit.core.types import Message, MessageSpeaker


@pytest.fixture
def default_config() -> HandoffConfig:
    """Create a default HandoffConfig for testing."""
    return HandoffConfig()


@pytest.fixture
def orchestrator(default_config: HandoffConfig) -> HandoffOrchestrator:
    """Create a HandoffOrchestrator instance for testing."""
    return HandoffOrchestrator(config=default_config)


@pytest.fixture
def sample_message() -> Message:
    """Create a sample user message for testing."""
    return Message(
        speaker="user",
        content="Hello, I need help with my order.",
    )


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create a sample conversation history for testing."""
    return [
        Message(speaker="user", content="Hi, I have a problem with my order."),
        Message(speaker="ai", content="I'm sorry to hear that. What seems to be the issue?"),
        Message(speaker="user", content="The item arrived damaged."),
        Message(speaker="ai", content="I apologize for the inconvenience. Let me help you with that."),
        Message(speaker="user", content="I want to speak to a human agent."),
    ]
