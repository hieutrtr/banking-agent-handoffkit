"""Tests for Orchestrator Fallback Integration (Story 3.10)."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handoffkit.core.config import HandoffConfig, RoutingConfig
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
from handoffkit.fallback.models import FallbackReason
from handoffkit.integrations.zendesk import ZendeskIntegration
from handoffkit.integrations.intercom import IntercomIntegration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    return [
        Message(
            speaker=MessageSpeaker.USER,
            content="I need help with my account",
            timestamp="2024-01-15T10:00:00Z",
        )
    ]


@pytest.fixture
def sample_context(sample_messages):
    """Create sample conversation context."""
    return ConversationContext(
        conversation_id="conv-test-123",
        user_id="user-456",
        messages=sample_messages,
    )


# ============================================================================
# Orchestrator Fallback Tests
# ============================================================================


class TestOrchestratorFallback:
    """Tests for orchestrator fallback functionality."""

    @pytest.mark.asyncio
    async def test_create_handoff_no_agents_available_fallback(self, sample_messages):
        """Test fallback when no agents are available."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_unassigned_ticket",
        ]

        # Mock no agents available
        mock_integration.check_agent_availability = AsyncMock(return_value=[])

        # Mock create_unassigned_ticket
        mock_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
            ticket_url="https://test.zendesk.com/tickets/456",
        )
        mock_integration.create_unassigned_ticket = AsyncMock(return_value=mock_result)

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify fallback was used
        assert result.success is True
        assert result.metadata["agent_availability"]["checked"] is True
        assert result.metadata["agent_availability"]["agents_available"] == 0
        assert result.metadata["agent_availability"]["assignment_method"] == "unassigned_fallback"

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_unassigned_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_handoff_agent_assignment_fallback(self, sample_messages):
        """Test fallback when agent assignment fails."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
            "convert_to_unassigned",
        ]

        # Mock available agents
        available_agents = [
            {"id": "123", "name": "John Agent", "email": "john@example.com"},
        ]
        mock_integration.check_agent_availability = AsyncMock(return_value=available_agents)

        # Mock ticket creation success
        mock_create_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
            ticket_url="https://test.zendesk.com/tickets/456",
        )
        mock_integration.create_ticket = AsyncMock(return_value=mock_create_result)

        # Mock assignment failure
        mock_integration.assign_to_agent = AsyncMock(return_value=False)

        # Mock convert to unassigned
        mock_integration.convert_to_unassigned = AsyncMock(return_value=True)

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify ticket was created but assignment failed
        assert result.success is True
        assert result.assigned_agent is None  # No agent assigned

        # Verify calls
        mock_integration.check_agent_availability.assert_called_once()
        mock_integration.create_ticket.assert_called_once()
        mock_integration.assign_to_agent.assert_called_once()
        mock_integration.convert_to_unassigned.assert_called_once_with("ticket-456", "agent_assignment_failed")

    @pytest.mark.asyncio
    async def test_create_handoff_integration_error_fallback(self, sample_messages):
        """Test fallback when integration throws error."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]

        # Mock availability check throwing error
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("API Error")
        )

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify fallback ticket was created
        assert result.success is True
        assert "fallback_ticket" in result.metadata
        assert result.metadata["fallback_reason"] == "integration_error"
        assert result.metadata["assignment_method"] == "fallback_local_storage"
        assert result.metadata["retry_scheduled"] is True

    @pytest.mark.asyncio
    async def test_create_handoff_no_integration_fallback(self, sample_messages):
        """Test fallback when no integration is configured."""
        orchestrator = HandoffOrchestrator(helpdesk="custom")  # No integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify fallback ticket was created
        assert result.success is True
        assert "fallback_ticket" in result.metadata
        assert result.metadata["fallback_reason"] == "integration_offline"
        assert result.metadata["assignment_method"] == "fallback_local_storage"

    @pytest.mark.asyncio
    async def test_create_handoff_with_fallback_disabled(self, sample_messages):
        """Test behavior when fallback is not supported by integration."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock integration without fallback support
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",  # No create_unassigned_ticket
        ]

        # Mock no agents available
        mock_integration.check_agent_availability = AsyncMock(return_value=[])

        # Mock regular ticket creation
        mock_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
            ticket_url="https://test.zendesk.com/tickets/456",
        )
        mock_integration.create_ticket = AsyncMock(return_value=mock_result)

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Should use regular create_ticket
        assert result.success is True
        assert result.metadata["agent_availability"]["assignment_method"] == "unassigned_fallback"

        # Verify create_unassigned_ticket was NOT called
        assert not hasattr(mock_integration, 'create_unassigned_ticket')
        mock_integration.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_ticket_storage_and_retry(self, sample_messages):
        """Test that fallback tickets are stored and queued for retry."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock integration that throws error
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify fallback was created
        assert result.success is True
        assert "fallback_ticket" in result.metadata

        # Verify ticket was saved to storage
        fallback_id = result.handoff_id
        saved_ticket = await orchestrator._fallback_storage.get_ticket(fallback_id)
        assert saved_ticket is not None
        assert saved_ticket.integration_name == "zendesk"
        assert saved_ticket.fallback_reason == FallbackReason.INTEGRATION_ERROR

        # Verify ticket was added to retry queue
        assert await orchestrator._fallback_retry_queue.get_pending_count() == 1

    @pytest.mark.asyncio
    async def test_user_notification_on_fallback(self, sample_messages):
        """Test that users are notified when fallback occurs."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Mock integration error
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("API Error")
        )

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify user notification is included
        assert result.success is True
        assert "user_notification" in result.metadata
        assert "temporarily offline" in result.metadata["user_notification"]

    @pytest.mark.asyncio
    async def test_fallback_with_different_reasons(self, sample_messages):
        """Test fallback with different fallback reasons."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Test integration offline
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=httpx.ConnectError("Network error")
        )

        orchestrator._integration = mock_integration

        result = await orchestrator.create_handoff(sample_messages)
        assert result.metadata["fallback_reason"] == "integration_offline"

        # Test no agents available
        mock_integration.check_agent_availability = AsyncMock(return_value=[])
        mock_integration.create_unassigned_ticket = AsyncMock(
            return_value=HandoffResult(
                success=True,
                handoff_id="handoff-123",
                status=HandoffStatus.PENDING,
                ticket_id="ticket-456",
            )
        )

        result = await orchestrator.create_handoff(sample_messages)
        assert result.metadata["agent_availability"]["assignment_method"] == "unassigned_fallback"

    @pytest.mark.asyncio
    async def test_fallback_metadata_preservation(self, sample_messages):
        """Test that all metadata is preserved in fallback tickets."""
        orchestrator = HandoffOrchestrator(helpdesk="zendesk")

        # Add metadata to handoff
        metadata = {
            "user_id": "test-user-123",
            "channel": "web",
            "custom_field": "custom_value",
        }

        # Mock integration error
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = ["check_agent_availability"]
        mock_integration.check_agent_availability = AsyncMock(
            side_effect=Exception("API Error")
        )

        orchestrator._integration = mock_integration

        # Create handoff with metadata
        result = await orchestrator.create_handoff(sample_messages, metadata=metadata)

        # Verify metadata is preserved
        assert result.success is True
        fallback_ticket_data = result.metadata["fallback_ticket"]
        assert "original_context" in fallback_ticket_data
        assert "metadata" in fallback_ticket_data["original_context"]