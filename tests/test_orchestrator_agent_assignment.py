"""Tests for Orchestrator Agent Assignment (Story 3.8 Task 7)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    MessageSpeaker,
)
from handoffkit.integrations.zendesk import ZendeskIntegration
from handoffkit.integrations.intercom import IntercomIntegration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create sample messages for testing."""
    return [
        Message(
            speaker=MessageSpeaker.USER,
            content="I need help with my account",
            timestamp="2024-01-15T10:00:00Z",
        )
    ]


@pytest.fixture
def sample_context(sample_messages: list[Message]) -> ConversationContext:
    """Create sample conversation context."""
    return ConversationContext(
        conversation_id="conv-test-123",
        user_id="user-456",
        messages=sample_messages,
    )


@pytest.fixture
def sample_decision() -> HandoffDecision:
    """Create sample handoff decision."""
    return HandoffDecision(
        should_handoff=True,
        priority=HandoffPriority.MEDIUM,
        trigger_results=[],
    )


# ============================================================================
# Orchestrator Agent Assignment Tests
# ============================================================================


class TestOrchestratorAgentAssignment:
    """Tests for orchestrator agent assignment functionality."""

    @pytest.mark.asyncio
    async def test_create_handoff_with_available_agents(self) -> None:
        """Test handoff when agents are available."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]
        mock_integration.check_agent_availability = AsyncMock(
            return_value=[
                {
                    "id": "123",
                    "name": "John Agent",
                    "email": "john@example.com",
                    "status": "online",
                    "platform": "zendesk",
                }
            ]
        )
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
                ticket_url="https://test.zendesk.com/tickets/456",
            )
        )
        mock_integration.assign_to_agent = AsyncMock(return_value=True)

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results
        assert result.success is True
        assert result.assigned_agent == "John Agent"
        assert result.metadata["agent_availability"]["checked"] is True
        assert result.metadata["agent_availability"]["agents_available"] == 1
        assert result.metadata["agent_availability"]["assigned_agent"] == "John Agent"
        assert result.metadata["agent_availability"]["assignment_method"] == "availability_check"

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()
        mock_integration.assign_to_agent.assert_called_once_with("ticket-456", "123")

    @pytest.mark.asyncio
    async def test_create_handoff_no_agents_available(self) -> None:
        """Test handoff when no agents are available."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
        ]
        mock_integration.check_agent_availability = AsyncMock(return_value=[])
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
                ticket_url="https://test.zendesk.com/tickets/456",
            )
        )

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results
        assert result.success is True
        assert result.assigned_agent is None  # No agent assigned
        assert result.metadata["agent_availability"]["checked"] is True
        assert result.metadata["agent_availability"]["agents_available"] == 0
        assert result.metadata["agent_availability"]["assignment_method"] == "unassigned_fallback"

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_handoff_agent_assignment_fails(self) -> None:
        """Test handoff when agent assignment fails."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]
        mock_integration.check_agent_availability = AsyncMock(
            return_value=[
                {
                    "id": "123",
                    "name": "John Agent",
                    "email": "john@example.com",
                    "status": "online",
                    "platform": "zendesk",
                }
            ]
        )
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
                ticket_url="https://test.zendesk.com/tickets/456",
            )
        )
        mock_integration.assign_to_agent = AsyncMock(return_value=False)

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results
        assert result.success is True
        assert result.assigned_agent is None  # Assignment failed
        assert result.metadata["agent_availability"]["checked"] is True
        assert result.metadata["agent_availability"]["agents_available"] == 1

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()
        mock_integration.assign_to_agent.assert_called_once_with("ticket-456", "123")

    @pytest.mark.asyncio
    async def test_create_handoff_availability_check_fails(self) -> None:
        """Test handoff when availability check fails."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
        ]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("API Error")
        )
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
                ticket_url="https://test.zendesk.com/tickets/456",
            )
        )

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results
        assert result.success is True
        assert result.assigned_agent is None  # No agent assigned due to error
        assert result.metadata["agent_availability"]["checked"] is True
        assert result.metadata["agent_availability"]["agents_available"] == 0
        assert result.metadata["agent_availability"]["assignment_method"] == "unassigned_fallback"

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_handoff_integration_without_availability_support(self) -> None:
        """Test handoff with integration that doesn't support availability checking."""
        orchestrator = HandoffOrchestrator(helpdesk="custom")

        # Mock a custom integration without availability support
        mock_integration = MagicMock()
        mock_integration.integration_name = "custom"
        mock_integration.supported_features = ["create_ticket"]  # No availability support
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
            )
        )

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results - should create ticket without checking availability
        assert result.success is True
        assert result.metadata.get("agent_availability") is None  # No availability info when not supported

        # Verify calls
        mock_integration.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_handoff_intercom_with_availability(self) -> None:
        """Test handoff with Intercom integration."""
        orchestrator = HandoffOrchestrator(helpdesk="intercom")

        # Mock the integration
        mock_integration = MagicMock(spec=IntercomIntegration)
        mock_integration.integration_name = "intercom"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]
        mock_integration.check_agent_availability = AsyncMock(
            return_value=[
                {
                    "id": "456",
                    "name": "Jane Admin",
                    "email": "jane@example.com",
                    "status": "available",
                    "platform": "intercom",
                }
            ]
        )
        mock_integration.create_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-789",
                status=HandoffStatus.PENDING,
                ticket_id="conv-123",
            )
        )
        mock_integration.assign_to_agent = AsyncMock(return_value=True)

        # Set the mock integration
        orchestrator._integration = mock_integration

        # Create handoff
        messages = [Message(speaker=MessageSpeaker.USER, content="Help!")]
        result = await orchestrator.create_handoff(messages)

        # Verify results
        assert result.success is True
        assert result.assigned_agent == "Jane Admin"
        assert result.metadata["agent_availability"]["assigned_agent"] == "Jane Admin"

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()
        mock_integration.assign_to_agent.assert_called_once_with("conv-123", "456")

    @pytest.mark.asyncio
    async def test_orchestrator_helper_method(self) -> None:
        """Test the _check_agent_availability_with_fallback helper method."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock integration with availability support
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            return_value=[
                {
                    "id": "123",
                    "name": "Test Agent",
                    "email": "test@example.com",
                }
            ]
        )

        # Test the helper method
        agents = await orchestrator._check_agent_availability_with_fallback(mock_integration)

        assert len(agents) == 1
        assert agents[0]["name"] == "Test Agent"
        mock_integration.check_agent_availability.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_helper_method_no_support(self) -> None:
        """Test helper method with integration that doesn't support availability."""
        orchestrator = HandoffOrchestrator(helpdesk="custom")

        # Mock integration without availability support
        mock_integration = MagicMock()
        mock_integration.integration_name = "custom"
        mock_integration.supported_features = ["create_ticket"]  # No availability

        # Test the helper method
        agents = await orchestrator._check_agent_availability_with_fallback(mock_integration)

        assert agents is None  # Should return None when not supported
        mock_integration.check_agent_availability.assert_not_called()

    @pytest.mark.asyncio
    async def test_orchestrator_helper_method_error(self) -> None:
        """Test helper method when availability check fails."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock integration that throws error
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Test the helper method
        agents = await orchestrator._check_agent_availability_with_fallback(mock_integration)

        assert len(agents) == 0  # Should return empty list on error
        mock_integration.check_agent_availability.assert_called_once()