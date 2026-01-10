"""Tests for Round Robin Agent Assignment (Story 3.9)."""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handoffkit.core.config import HandoffConfig, RoutingConfig
from handoffkit.core.orchestrator import HandoffOrchestrator
from handoffkit.core.round_robin import AssignmentHistory, AssignmentRecord, RoundRobinAssigner
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
def sample_agents():
    """Create sample agents for testing."""
    return [
        {"id": "agent-1", "name": "Alice Agent", "email": "alice@example.com", "status": "online"},
        {"id": "agent-2", "name": "Bob Agent", "email": "bob@example.com", "status": "online"},
        {"id": "agent-3", "name": "Charlie Agent", "email": "charlie@example.com", "status": "online"},
    ]


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
def round_robin_config():
    """Create round-robin configuration."""
    return RoutingConfig(
        round_robin_enabled=True,
        round_robin_rotation_window_minutes=5,
        round_robin_history_size=100,
        round_robin_fallback_retry_attempts=3,
    )


# ============================================================================
# AssignmentHistory Tests
# ============================================================================


class TestAssignmentHistory:
    """Tests for AssignmentHistory class."""

    @pytest.mark.asyncio
    async def test_record_assignment(self):
        """Test recording assignments."""
        history = AssignmentHistory(max_size=10)

        # Record an assignment
        await history.record_assignment("agent-1", "handoff-123")

        # Check it was recorded
        assert history.size == 1
        assert history.was_recently_assigned("agent-1", timedelta(minutes=1))

    @pytest.mark.asyncio
    async def test_was_recently_assigned(self):
        """Test checking recent assignments."""
        history = AssignmentHistory()
        agent_id = "agent-1"

        # Record assignment 10 minutes ago
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        history._agent_last_assignment[agent_id] = old_time

        # Should not be recent for 5 minute window
        assert not history.was_recently_assigned(agent_id, timedelta(minutes=5))

        # Should be recent for 15 minute window
        assert history.was_recently_assigned(agent_id, timedelta(minutes=15))

    @pytest.mark.asyncio
    async def test_circular_buffer_cleanup(self):
        """Test circular buffer cleanup."""
        history = AssignmentHistory(max_size=3)

        # Add 5 assignments
        for i in range(5):
            await history.record_assignment(f"agent-{i}", f"handoff-{i}")

        # Should only keep last 3
        assert history.size == 3

    @pytest.mark.asyncio
    async def test_cleanup_old_records(self):
        """Test cleanup of old records."""
        history = AssignmentHistory()

        # Add old and new records
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        new_time = datetime.now(timezone.utc)

        history._assignments.extend([
            AssignmentRecord("agent-old", "handoff-old", old_time),
            AssignmentRecord("agent-new", "handoff-new", new_time),
        ])
        history._agent_last_assignment = {
            "agent-old": old_time,
            "agent-new": new_time,
        }

        # Cleanup records older than 24 hours
        removed = await history.cleanup_old_records(timedelta(hours=24))

        assert removed == 1
        assert history.size == 1
        assert "agent-old" not in history._agent_last_assignment
        assert "agent-new" in history._agent_last_assignment


# ============================================================================
# RoundRobinAssigner Tests
# ============================================================================


class TestRoundRobinAssigner:
    """Tests for RoundRobinAssigner class."""

    @pytest.mark.asyncio
    async def test_basic_round_robin_rotation(self, sample_agents):
        """Test basic round-robin rotation."""
        assigner = RoundRobinAssigner(rotation_window_minutes=0)  # No rotation window for testing

        # Select agents in sequence
        agent1 = await assigner.select_agent(sample_agents, "handoff-1")
        agent2 = await assigner.select_agent(sample_agents, "handoff-2")
        agent3 = await assigner.select_agent(sample_agents, "handoff-3")

        # Should rotate through agents
        assert agent1["id"] == "agent-1"
        assert agent2["id"] == "agent-2"
        assert agent3["id"] == "agent-3"

    @pytest.mark.asyncio
    async def test_rotation_wraps_around(self, sample_agents):
        """Test that rotation wraps around after last agent."""
        assigner = RoundRobinAssigner(rotation_window_minutes=0)  # No rotation window for testing

        # Select more agents than available
        agents = []
        for i in range(5):
            agent = await assigner.select_agent(sample_agents, f"handoff-{i}")
            agents.append(agent)

        # Should wrap around
        assert agents[0]["id"] == "agent-1"
        assert agents[1]["id"] == "agent-2"
        assert agents[2]["id"] == "agent-3"
        assert agents[3]["id"] == "agent-1"  # Wrapped around
        assert agents[4]["id"] == "agent-2"  # Continued rotation

    @pytest.mark.asyncio
    async def test_skips_recently_assigned_agents(self, sample_agents):
        """Test that recently assigned agents are skipped."""
        assigner = RoundRobinAssigner(rotation_window_minutes=60)  # 1 hour window

        # Assign to first agent
        agent1 = await assigner.select_agent(sample_agents, "handoff-1")
        assert agent1["id"] == "agent-1"

        # Try to assign again immediately - should skip agent-1
        agent2 = await assigner.select_agent(sample_agents, "handoff-2")

        # Should skip agent-1 (assigned recently) and assign next available
        assert agent2["id"] in ["agent-2", "agent-3"]  # Could be either
        assert agent2["id"] != "agent-1"  # But definitely not agent-1

    @pytest.mark.asyncio
    async def test_all_agents_recently_assigned_fallback(self, sample_agents):
        """Test fallback when all agents were recently assigned."""
        assigner = RoundRobinAssigner(rotation_window_minutes=60)

        # Assign to all agents
        for i in range(len(sample_agents)):
            await assigner.select_agent(sample_agents, f"handoff-{i}")

        # Try to assign again immediately
        with patch.object(assigner._logger, "warning") as mock_warning:
            agent = await assigner.select_agent(sample_agents, "handoff-next")

            # Should use fallback and assign an agent (any agent since all were assigned)
            assert agent["id"] in ["agent-1", "agent-2", "agent-3"]
            assert agent is not None
            mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_agents_list(self):
        """Test with empty agents list."""
        assigner = RoundRobinAssigner()

        agent = await assigner.select_agent([], "handoff-1")
        assert agent is None

    @pytest.mark.asyncio
    async def test_performance_requirement(self, sample_agents):
        """Test that assignment completes in <100ms."""
        assigner = RoundRobinAssigner()

        # Measure assignment time
        start_time = time.time()
        agent = await assigner.select_agent(sample_agents, "handoff-1")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to ms

        # Should complete in under 100ms
        assert response_time < 100
        assert agent is not None

    @pytest.mark.asyncio
    async def test_thread_safety(self, sample_agents):
        """Test thread safety with concurrent assignments."""
        assigner = RoundRobinAssigner()

        # Create multiple concurrent assignment tasks
        tasks = []
        for i in range(10):
            task = assigner.select_agent(sample_agents, f"handoff-{i}")
            tasks.append(task)

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

        # All assignments should succeed
        assert len(results) == 10
        assert all(agent is not None for agent in results)

        # Should have distributed across agents
        assigned_agents = [agent["id"] for agent in results]
        assert len(set(assigned_agents)) >= 2  # Should use multiple agents

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting assignment statistics."""
        assigner = RoundRobinAssigner(
            rotation_window_minutes=10,
            assignment_history_size=500,
        )

        stats = assigner.get_statistics()

        assert stats["rotation_window_minutes"] == 10
        assert stats["current_rotation_index"] == 0
        assert stats["total_assignments"] == 0


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================


class TestOrchestratorRoundRobinIntegration:
    """Tests for round-robin integration with HandoffOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_round_robin(self, sample_messages, round_robin_config):
        """Test that orchestrator uses round-robin assignment."""
        # Create orchestrator with round-robin enabled
        config = HandoffConfig(routing=round_robin_config)
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]

        # Mock available agents
        available_agents = [
            {"id": "agent-1", "name": "Alice", "email": "alice@example.com"},
            {"id": "agent-2", "name": "Bob", "email": "bob@example.com"},
        ]
        mock_integration.check_agent_availability = AsyncMock(return_value=available_agents)

        # Mock ticket creation
        mock_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
        )
        mock_integration.create_ticket = AsyncMock(return_value=mock_result)
        mock_integration.assign_to_agent = AsyncMock(return_value=True)

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Verify round-robin was used
        assert result.success is True
        assert result.metadata["agent_availability"]["assignment_method"] == "round_robin"
        mock_integration.assign_to_agent.assert_called_once_with("ticket-456", "agent-1")

    @pytest.mark.asyncio
    async def test_orchestrator_round_robin_disabled(self, sample_messages):
        """Test that orchestrator skips round-robin when disabled."""
        # Create orchestrator with round-robin disabled
        config = HandoffConfig(
            routing=RoutingConfig(round_robin_enabled=False)
        )
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]

        # Mock available agents
        available_agents = [
            {"id": "agent-1", "name": "Alice", "email": "alice@example.com"},
            {"id": "agent-2", "name": "Bob", "email": "bob@example.com"},
        ]
        mock_integration.check_agent_availability = AsyncMock(return_value=available_agents)

        # Mock ticket creation
        mock_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
        )
        mock_integration.create_ticket = AsyncMock(return_value=mock_result)
        mock_integration.assign_to_agent = AsyncMock(return_value=True)

        orchestrator._integration = mock_integration

        # Create handoff
        result = await orchestrator.create_handoff(sample_messages)

        # Should use first available agent method
        assert result.success is True
        assert result.metadata["agent_availability"]["assignment_method"] == "availability_check"
        mock_integration.assign_to_agent.assert_called_once_with("ticket-456", "agent-1")

    @pytest.mark.asyncio
    async def test_orchestrator_round_robin_fallback(self, sample_messages, round_robin_config):
        """Test orchestrator fallback when round-robin fails."""
        # Create orchestrator
        config = HandoffConfig(routing=round_robin_config)
        orchestrator = HandoffOrchestrator(helpdesk="zendesk", config=config)

        # Mock the integration
        mock_integration = MagicMock(spec=ZendeskIntegration)
        mock_integration.integration_name = "zendesk"
        mock_integration.supported_features = [
            "check_agent_availability",
            "create_ticket",
            "assign_to_agent",
        ]

        # Mock available agents
        available_agents = [
            {"id": "agent-1", "name": "Alice", "email": "alice@example.com"},
        ]
        mock_integration.check_agent_availability = AsyncMock(return_value=available_agents)

        # Mock ticket creation
        mock_result = HandoffResult(
            success=True,
            handoff_id="handoff-123",
            status=HandoffStatus.PENDING,
            ticket_id="ticket-456",
        )
        mock_integration.create_ticket = AsyncMock(return_value=mock_result)
        mock_integration.assign_to_agent = AsyncMock(return_value=True)

        orchestrator._integration = mock_integration

        # Force round-robin to fail by making select_agent return None
        with patch.object(orchestrator._get_round_robin_assigner("zendesk"), "select_agent", return_value=None):
            # Create handoff
            result = await orchestrator.create_handoff(sample_messages)

            # Should still succeed using fallback
            assert result.success is True
            assert result.metadata["agent_availability"]["assignment_method"] == "availability_check"

    @pytest.mark.asyncio
    async def test_multiple_integrations_separate_state(self, sample_messages, round_robin_config):
        """Test that each integration has separate round-robin state."""
        # Create orchestrator
        config = HandoffConfig(routing=round_robin_config)
        orchestrator = HandoffOrchestrator(helpdesk="custom", config=config)

        # Mock Zendesk integration
        mock_zendesk = MagicMock(spec=ZendeskIntegration)
        mock_zendesk.integration_name = "zendesk"
        mock_zendesk.supported_features = ["check_agent_availability", "create_ticket"]
        mock_zendesk.check_agent_availability = AsyncMock(return_value=[
            {"id": "zendesk-agent-1", "name": "Zendesk Agent", "email": "zk@example.com"}
        ])
        mock_zendesk.create_ticket = AsyncMock(return_value=HandoffResult(
            success=True,
            handoff_id="zk-123",
            status=HandoffStatus.PENDING,
            ticket_id="zk-ticket-456",
        ))

        # Mock Intercom integration
        mock_intercom = MagicMock(spec=IntercomIntegration)
        mock_intercom.integration_name = "intercom"
        mock_intercom.supported_features = ["check_agent_availability", "create_ticket"]
        mock_intercom.check_agent_availability = AsyncMock(return_value=[
            {"id": "intercom-agent-1", "name": "Intercom Agent", "email": "ic@example.com"}
        ])
        mock_intercom.create_ticket = AsyncMock(return_value=HandoffResult(
            success=True,
            handoff_id="ic-123",
            status=HandoffStatus.PENDING,
            ticket_id="ic-ticket-456",
        ))

        # Test Zendesk assignment
        orchestrator.set_integration(mock_zendesk)
        result1 = await orchestrator.create_handoff(sample_messages)

        # Test Intercom assignment
        orchestrator.set_integration(mock_intercom)
        result2 = await orchestrator.create_handoff(sample_messages)

        # Both should succeed with their respective agents
        assert result1.success is True
        assert result1.metadata["agent_availability"]["assigned_agent"] == "Zendesk Agent"

        assert result2.success is True
        assert result2.metadata["agent_availability"]["assigned_agent"] == "Intercom Agent"