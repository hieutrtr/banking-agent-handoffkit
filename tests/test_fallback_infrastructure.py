"""Tests for Fallback Ticket Creation Infrastructure (Story 3.10)."""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from handoffkit.core.types import (
    ConversationContext,
    HandoffDecision,
    HandoffPriority,
    HandoffResult,
    HandoffStatus,
    Message,
    MessageSpeaker,
)
from handoffkit.fallback import FallbackNotifier, RetryQueue, RetryScheduler, FallbackStorage
from handoffkit.fallback.models import (
    FallbackReason,
    FallbackStatus,
    FallbackTicket,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_context():
    """Create sample conversation context."""
    return ConversationContext(
        conversation_id="conv-test-123",
        user_id="user-456",
        messages=[
            Message(
                speaker=MessageSpeaker.USER,
                content="I need help with my account",
                timestamp="2024-01-15T10:00:00Z",
            )
        ],
    )


@pytest.fixture
def sample_decision():
    """Create sample handoff decision."""
    return HandoffDecision(
        should_handoff=True,
        priority=HandoffPriority.MEDIUM,
        trigger_results=[],
    )


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Fallback Models Tests
# ============================================================================


class TestFallbackModels:
    """Tests for fallback data models."""

    def test_fallback_ticket_creation(self):
        """Test creating a fallback ticket."""
        ticket = FallbackTicket(
            fallback_id="fb-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test", "body": "Test body"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={"test": "data"},
        )

        assert ticket.fallback_id == "fb-123"
        assert ticket.status == FallbackStatus.PENDING
        assert ticket.retry_count == 0

    def test_is_retryable(self):
        """Test retryable status logic."""
        ticket = FallbackTicket(
            fallback_id="fb-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={},
        )

        # New ticket should be retryable
        assert ticket.is_retryable()

        # Assigned ticket should not be retryable
        ticket.status = FallbackStatus.ASSIGNED
        assert not ticket.is_retryable()

        # Failed ticket should not be retryable
        ticket.status = FallbackStatus.FAILED
        assert not ticket.is_retryable()

        # Ticket with max retries should not be retryable
        ticket.status = FallbackStatus.PENDING
        ticket.retry_count = 12
        assert not ticket.is_retryable()

    def test_should_retry_now(self):
        """Test retry timing logic."""
        ticket = FallbackTicket(
            fallback_id="fb-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={},
        )

        # New ticket should retry immediately
        assert ticket.should_retry_now()

        # Ticket with retry_after in future should not retry
        ticket.retry_after = datetime.now(timezone.utc) + timedelta(minutes=10)
        assert not ticket.should_retry_now()

        # Ticket with retry_after in past should retry
        ticket.retry_after = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert ticket.should_retry_now()

    def test_increment_retry(self):
        """Test retry increment."""
        ticket = FallbackTicket(
            fallback_id="fb-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={},
        )

        initial_count = ticket.retry_count
        ticket.increment_retry()
        assert ticket.retry_count == initial_count + 1
        assert ticket.last_retry_at is not None

    def test_user_message_generation(self):
        """Test user message generation."""
        ticket = FallbackTicket(
            fallback_id="fb-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={},
            fallback_reason=FallbackReason.NO_AGENTS_AVAILABLE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={},
            estimated_wait_minutes=15,
            queue_position=3,
        )

        message = ticket.get_user_message()
        assert "All agents are currently busy" in message
        assert "Queue position: 3" in message
        assert "Estimated wait time: 15 minutes" in message

        # Test integration offline message
        ticket.fallback_reason = FallbackReason.INTEGRATION_OFFLINE
        message = ticket.get_user_message()
        assert "temporarily offline" in message
        assert "fb-123" in message


# ============================================================================
# Fallback Storage Tests
# ============================================================================


class TestFallbackStorage:
    """Tests for fallback ticket storage."""

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create storage instance with temp directory."""
        return FallbackStorage(str(temp_storage_dir))

    @pytest.mark.asyncio
    async def test_save_and_retrieve_ticket(self, storage, sample_context, sample_decision):
        """Test saving and retrieving a ticket."""
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

        # Save ticket
        await storage.save_ticket(ticket)

        # Retrieve ticket
        retrieved = await storage.get_ticket("fb-test-123")
        assert retrieved is not None
        assert retrieved.fallback_id == "fb-test-123"
        assert retrieved.integration_name == "zendesk"
        assert retrieved.fallback_reason == FallbackReason.INTEGRATION_OFFLINE

    @pytest.mark.asyncio
    async def test_list_tickets(self, storage, sample_context, sample_decision):
        """Test listing tickets with filters."""
        # Create multiple tickets
        for i in range(3):
            ticket = FallbackTicket(
                fallback_id=f"fb-test-{i}",
                handoff_id=f"handoff-{i}",
                integration_name="zendesk" if i < 2 else "intercom",
                ticket_data={"subject": f"Test {i}"},
                fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
                priority=HandoffPriority.MEDIUM,
                created_at=datetime.now(timezone.utc),
                original_context=sample_context.model_dump(),
            )
            await storage.save_ticket(ticket)

        # List all tickets
        all_tickets = await storage.list_tickets()
        assert len(all_tickets) == 3

        # List by integration
        zendesk_tickets = await storage.list_tickets(integration_name="zendesk")
        assert len(zendesk_tickets) == 2

        # List with limit
        limited_tickets = await storage.list_tickets(limit=2)
        assert len(limited_tickets) == 2

    @pytest.mark.asyncio
    async def test_update_ticket(self, storage, sample_context, sample_decision):
        """Test updating a ticket."""
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

        await storage.save_ticket(ticket)

        # Update ticket
        ticket.status = FallbackStatus.ASSIGNED
        ticket.retry_count = 1
        success = await storage.update_ticket(ticket)
        assert success is True

        # Verify update
        updated = await storage.get_ticket("fb-test-123")
        assert updated.status == FallbackStatus.ASSIGNED
        assert updated.retry_count == 1

    @pytest.mark.asyncio
    async def test_delete_ticket(self, storage, sample_context, sample_decision):
        """Test deleting a ticket."""
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

        await storage.save_ticket(ticket)

        # Delete ticket
        success = await storage.delete_ticket("fb-test-123")
        assert success is True

        # Verify deletion
        deleted = await storage.get_ticket("fb-test-123")
        assert deleted is None

    @pytest.mark.asyncio
    async def test_cleanup_old_tickets(self, storage, sample_context, sample_decision):
        """Test cleaning up old tickets."""
        # Create old ticket
        old_ticket = FallbackTicket(
            fallback_id="fb-old-123",
            handoff_id="handoff-old",
            integration_name="zendesk",
            ticket_data={"subject": "Old"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc) - timedelta(days=31),
            original_context=sample_context.model_dump(),
        )

        # Create recent ticket
        recent_ticket = FallbackTicket(
            fallback_id="fb-recent-123",
            handoff_id="handoff-recent",
            integration_name="zendesk",
            ticket_data={"subject": "Recent"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

        await storage.save_ticket(old_ticket)
        await storage.save_ticket(recent_ticket)

        # Cleanup tickets older than 30 days
        cleaned = await storage.cleanup_old_tickets(max_age_days=30)
        assert cleaned == 1

        # Verify old ticket deleted
        assert await storage.get_ticket("fb-old-123") is None
        assert await storage.get_ticket("fb-recent-123") is not None


# ============================================================================
# Retry Queue Tests
# ============================================================================


class TestRetryQueue:
    """Tests for retry queue management."""

    @pytest.fixture
    def queue(self):
        """Create retry queue instance."""
        return RetryQueue()

    @pytest.fixture
    def sample_ticket(self, sample_context, sample_decision):
        """Create sample fallback ticket."""
        return FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue(self, queue, sample_ticket):
        """Test basic enqueue and dequeue operations."""
        # Enqueue ticket
        await queue.enqueue(sample_ticket)

        # Check queue size
        assert await queue.get_pending_count() == 1

        # Dequeue ticket
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.fallback_id == "fb-test-123"

        # Queue should be empty
        assert await queue.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_retry_timing(self, queue):
        """Test retry timing logic."""
        # Create ticket that was just retried
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            last_retry_at=datetime.now(timezone.utc),
            retry_count=1,
            original_context={},
        )

        await queue.enqueue(ticket)

        # Should not be ready immediately (exponential backoff)
        ready = await queue.peek()
        assert ready is None

        # Should be ready after delay
        await asyncio.sleep(0.1)  # Small delay for test
        ticket.last_retry_at = datetime.now(timezone.utc) - timedelta(minutes=6)

        # Re-enqueue with updated time
        await queue.enqueue(ticket)
        ready = await queue.peek()
        assert ready is not None

    @pytest.mark.asyncio
    async def test_non_retryable_tickets(self, queue):
        """Test that non-retryable tickets are not dequeued."""
        # Create assigned ticket
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            status=FallbackStatus.ASSIGNED,
            original_context={},
        )

        await queue.enqueue(ticket)

        # Should not dequeue assigned ticket
        dequeued = await queue.dequeue()
        assert dequeued is None

    @pytest.mark.asyncio
    async def test_remove_ticket(self, queue, sample_ticket):
        """Test removing specific ticket from queue."""
        await queue.enqueue(sample_ticket)

        # Remove ticket
        removed = await queue.remove_ticket("fb-test-123")
        assert removed is True

        # Queue should be empty
        assert await queue.get_pending_count() == 0

    @pytest.mark.asyncio
    async def test_clear_expired_tickets(self, queue):
        """Test clearing expired tickets."""
        # Create assigned ticket
        assigned_ticket = FallbackTicket(
            fallback_id="fb-assigned-123",
            handoff_id="handoff-assigned",
            integration_name="zendesk",
            ticket_data={"subject": "Assigned"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            status=FallbackStatus.ASSIGNED,
            original_context={},
        )

        # Create failed ticket
        failed_ticket = FallbackTicket(
            fallback_id="fb-failed-123",
            handoff_id="handoff-failed",
            integration_name="zendesk",
            ticket_data={"subject": "Failed"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            status=FallbackStatus.FAILED,
            original_context={},
        )

        # Create retryable ticket
        retryable_ticket = FallbackTicket(
            fallback_id="fb-retryable-123",
            handoff_id="handoff-retryable",
            integration_name="zendesk",
            ticket_data={"subject": "Retryable"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context={},
        )

        await queue.enqueue(assigned_ticket)
        await queue.enqueue(failed_ticket)
        await queue.enqueue(retryable_ticket)

        # Clear expired
        cleared = await queue.clear_expired_tickets()
        assert cleared == 2  # assigned and failed tickets

        # Only retryable ticket should remain
        assert await queue.get_pending_count() == 1


# ============================================================================
# Fallback Notifier Tests
# ============================================================================


class TestFallbackNotifier:
    """Tests for fallback notifier."""

    @pytest.fixture
    def notifier(self):
        """Create notifier instance."""
        return FallbackNotifier()

    @pytest.fixture
    def sample_ticket(self, sample_context, sample_decision):
        """Create sample fallback ticket."""
        return FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test"},
            fallback_reason=FallbackReason.NO_AGENTS_AVAILABLE,
            priority=HandoffPriority.MEDIUM,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
            estimated_wait_minutes=15,
            queue_position=3,
        )

    @pytest.mark.asyncio
    async def test_notify_no_agents_available(self, notifier, sample_ticket):
        """Test notification for no agents available."""
        message = await notifier.notify_user(
            sample_ticket,
            queue_position=3,
            estimated_wait_minutes=15,
        )

        assert "All agents are currently busy" in message
        assert "Queue position: 3" in message
        assert "Estimated wait time: 15 minutes" in message
        assert "fb-test-123" in message

    @pytest.mark.asyncio
    async def test_notify_integration_offline(self, notifier, sample_ticket):
        """Test notification for integration offline."""
        sample_ticket.fallback_reason = FallbackReason.INTEGRATION_OFFLINE

        message = await notifier.notify_user(sample_ticket)

        assert "temporarily offline" in message
        assert "fb-test-123" in message
        assert "saved with reference" in message

    @pytest.mark.asyncio
    async def test_notify_assignment_failed(self, notifier, sample_ticket):
        """Test notification for assignment failure."""
        sample_ticket.fallback_reason = FallbackReason.AGENT_ASSIGNMENT_FAILED

        message = await notifier.notify_user(sample_ticket)

        assert "couldn't assign" in message
        assert "shortly" in message
        assert "fb-test-123" in message

    @pytest.mark.asyncio
    async def test_notify_assignment_success(self, notifier, sample_ticket):
        """Test notification of successful assignment."""
        message = await notifier.notify_assignment_success(
            sample_ticket,
            "ticket-789",
            "John Agent",
        )

        assert "Great news" in message
        assert "assigned to John Agent" in message
        assert "Ticket ID: ticket-789" in message

    @pytest.mark.asyncio
    async def test_notify_assignment_failure(self, notifier, sample_ticket):
        """Test notification of assignment failure."""
        message = await notifier.notify_assignment_failure(
            sample_ticket,
            max_retries_reached=True,
        )

        assert "apologize" in message
        assert "manually reviewed" in message
        assert "fb-test-123" in message


# ============================================================================
# Integration Tests
# ============================================================================


class TestFallbackIntegration:
    """Integration tests for fallback system components."""

    @pytest.mark.asyncio
    async def test_full_fallback_flow(self, temp_storage_dir, sample_context, sample_decision):
        """Test complete fallback flow."""
        # Initialize components
        storage = FallbackStorage(str(temp_storage_dir))
        queue = RetryQueue()
        notifier = FallbackNotifier()

        # Create fallback ticket
        ticket = FallbackTicket(
            fallback_id="fb-test-123",
            handoff_id="handoff-456",
            integration_name="zendesk",
            ticket_data={"subject": "Test Handoff", "body": "Test body"},
            fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
            priority=HandoffPriority.HIGH,
            created_at=datetime.now(timezone.utc),
            original_context=sample_context.model_dump(),
        )

        # Save ticket
        await storage.save_ticket(ticket)

        # Add to retry queue
        await queue.enqueue(ticket)

        # Notify user
        message = await notifier.notify_user(ticket)

        # Verify integration
        assert await storage.get_ticket("fb-test-123") is not None
        assert await queue.get_pending_count() == 1
        assert "temporarily offline" in message

    @pytest.mark.asyncio
    async def test_retry_scheduler_simulation(self, temp_storage_dir):
        """Test retry scheduler with simulated processing."""
        storage = FallbackStorage(str(temp_storage_dir))
        queue = RetryQueue()

        # Create tickets with different retry states
        tickets = []
        for i in range(3):
            ticket = FallbackTicket(
                fallback_id=f"fb-test-{i}",
                handoff_id=f"handoff-{i}",
                integration_name="zendesk",
                ticket_data={"subject": f"Test {i}"},
                fallback_reason=FallbackReason.INTEGRATION_OFFLINE,
                priority=HandoffPriority.MEDIUM,
                created_at=datetime.now(timezone.utc),
                retry_count=i,
                last_retry_at=datetime.now(timezone.utc) - timedelta(minutes=6),  # Ready for retry
                original_context={},
            )
            tickets.append(ticket)
            await storage.save_ticket(ticket)
            await queue.enqueue(ticket)

        # Process retry queue
        processed = 0
        while True:
            ticket = await queue.dequeue()
            if not ticket:
                break
            processed += 1

            # Simulate successful retry
            ticket.increment_retry()
            ticket.mark_assigned(f"ticket-{ticket.fallback_id}")
            await storage.update_ticket(ticket)

        assert processed == 3

        # Verify all tickets are marked as assigned
        for i in range(3):
            ticket = await storage.get_ticket(f"fb-test-{i}")
            assert ticket.status == FallbackStatus.ASSIGNED