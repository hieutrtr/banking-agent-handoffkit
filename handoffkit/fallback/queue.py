"""Retry queue management for fallback tickets."""

import asyncio
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from typing import Optional

from handoffkit.fallback.models import FallbackTicket
from handoffkit.utils.logging import get_logger


class RetryQueue:
    """Priority queue for managing fallback ticket retries.

    Uses a min-heap to efficiently manage tickets based on their next retry time.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize retry queue."""
        self._queue: list[tuple[datetime, str, FallbackTicket]] = []
        self._ticket_map: dict[str, FallbackTicket] = {}
        self._lock = asyncio.Lock()
        self._logger = get_logger("fallback.queue")

    async def enqueue(self, ticket: FallbackTicket) -> None:
        """Add a ticket to the retry queue.

        Args:
            ticket: The fallback ticket to retry
        """
        async with self._lock:
            try:
                # Calculate next retry time
                next_retry = self._calculate_next_retry_time(ticket)

                # Add to queue
                heappush(self._queue, (next_retry, ticket.fallback_id, ticket))
                self._ticket_map[ticket.fallback_id] = ticket

                self._logger.info(
                    "Ticket added to retry queue",
                    extra={
                        "fallback_id": ticket.fallback_id,
                        "next_retry": next_retry.isoformat(),
                        "retry_count": ticket.retry_count,
                        "queue_size": len(self._queue),
                    }
                )

            except Exception as e:
                self._logger.error(
                    f"Failed to enqueue ticket: {e}",
                    extra={"fallback_id": ticket.fallback_id, "error": str(e)},
                )
                raise

    async def dequeue(self) -> Optional[FallbackTicket]:
        """Remove and return the next ticket ready for retry.

        Returns:
            The next retryable ticket or None if queue is empty
        """
        async with self._lock:
            try:
                # Check if there are tickets ready to retry
                now = datetime.now(timezone.utc)

                while self._queue:
                    next_retry_time, fallback_id, ticket = self._queue[0]

                    # If ticket is ready to retry
                    if now >= next_retry_time:
                        # Verify ticket is still retryable
                        if ticket.is_retryable():
                            heappop(self._queue)
                            if fallback_id in self._ticket_map:
                                del self._ticket_map[fallback_id]

                            self._logger.info(
                                "Ticket dequeued for retry",
                                extra={
                                    "fallback_id": ticket.fallback_id,
                                    "retry_count": ticket.retry_count,
                                    "queue_size": len(self._queue),
                                }
                            )
                            return ticket
                        else:
                            # Ticket is no longer retryable, remove it
                            heappop(self._queue)
                            if fallback_id in self._ticket_map:
                                del self._ticket_map[fallback_id]
                            continue
                    else:
                        # No more tickets ready to retry
                        break

                return None

            except Exception as e:
                self._logger.error(f"Failed to dequeue ticket: {e}", extra={"error": str(e)})
                return None

    async def peek(self) -> Optional[FallbackTicket]:
        """Get the next ticket ready for retry without removing it.

        Returns:
            The next retryable ticket or None
        """
        async with self._lock:
            try:
                now = datetime.now(timezone.utc)

                # Find next ready ticket without removing it
                for next_retry_time, fallback_id, ticket in self._queue:
                    if now >= next_retry_time and ticket.is_retryable():
                        return ticket

                return None

            except Exception as e:
                self._logger.error(f"Failed to peek queue: {e}", extra={"error": str(e)})
                return None

    async def get_pending_count(self) -> int:
        """Get count of tickets pending retry.

        Returns:
            Number of tickets in queue
        """
        async with self._lock:
            return len(self._queue)

    async def get_retryable_count(self) -> int:
        """Get count of tickets that are retryable now.

        Returns:
            Number of tickets ready for retry
        """
        async with self._lock:
            try:
                now = datetime.now(timezone.utc)
                count = 0

                for next_retry_time, fallback_id, ticket in self._queue:
                    if now >= next_retry_time and ticket.is_retryable():
                        count += 1

                return count

            except Exception as e:
                self._logger.error(f"Failed to count retryable tickets: {e}", extra={"error": str(e)})
                return 0

    async def remove_ticket(self, fallback_id: str) -> bool:
        """Remove a specific ticket from the queue.

        Args:
            fallback_id: ID of ticket to remove

        Returns:
            True if ticket was found and removed
        """
        async with self._lock:
            try:
                # Find and remove from queue
                new_queue = []
                found = False

                for next_retry_time, ticket_id, ticket in self._queue:
                    if ticket_id == fallback_id:
                        found = True
                        continue
                    new_queue.append((next_retry_time, ticket_id, ticket))

                # Rebuild heap
                self._queue = new_queue
                # Note: heap property is maintained because we're removing elements

                # Remove from map
                if fallback_id in self._ticket_map:
                    del self._ticket_map[fallback_id]

                if found:
                    self._logger.info(
                        "Ticket removed from retry queue",
                        extra={"fallback_id": fallback_id, "queue_size": len(self._queue)},
                    )

                return found

            except Exception as e:
                self._logger.error(
                    f"Failed to remove ticket from queue: {e}",
                    extra={"fallback_id": fallback_id, "error": str(e)},
                )
                return False

    async def clear_expired_tickets(self) -> int:
        """Remove tickets that are no longer retryable.

        Returns:
            Number of tickets removed
        """
        async with self._lock:
            try:
                expired_count = 0
                new_queue = []

                for next_retry_time, fallback_id, ticket in self._queue:
                    if ticket.is_retryable():
                        new_queue.append((next_retry_time, fallback_id, ticket))
                    else:
                        expired_count += 1
                        if fallback_id in self._ticket_map:
                            del self._ticket_map[fallback_id]

                self._queue = new_queue

                if expired_count > 0:
                    self._logger.info(
                        f"Cleared {expired_count} expired tickets from queue",
                        extra={"cleared_count": expired_count, "remaining_count": len(self._queue)},
                    )

                return expired_count

            except Exception as e:
                self._logger.error(f"Failed to clear expired tickets: {e}", extra={"error": str(e)})
                return 0

    async def get_stats(self) -> dict:
        """Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        async with self._lock:
            try:
                retryable_count = await self.get_retryable_count()
                total_count = len(self._queue)

                # Calculate next retry time
                next_retry_time = None
                if self._queue:
                    next_retry_time, _, _ = self._queue[0]

                return {
                    "total_tickets": total_count,
                    "retryable_now": retryable_count,
                    "next_retry_time": next_retry_time.isoformat() if next_retry_time else None,
                    "ticket_map_size": len(self._ticket_map),
                }

            except Exception as e:
                self._logger.error(f"Failed to get queue stats: {e}", extra={"error": str(e)})
                return {}

    def _calculate_next_retry_time(self, ticket: FallbackTicket) -> datetime:
        """Calculate when a ticket should be retried next.

        Args:
            ticket: The fallback ticket

        Returns:
            Next retry time
        """
        if ticket.retry_after:
            return ticket.retry_after

        if not ticket.last_retry_at:
            # First retry - try immediately
            return datetime.now(timezone.utc)

        # Exponential backoff: start at 5 minutes, double each time, max 60 minutes
        base_delay = 5  # minutes
        max_delay = 60  # minutes
        delay = min(base_delay * (2 ** ticket.retry_count), max_delay)

        return ticket.last_retry_at + timedelta(minutes=delay)


class RetryScheduler:
    """Background scheduler for processing retry queue."""

    def __init__(
        self,
        queue: RetryQueue,
        storage,  # FallbackStorage instance
        check_interval: int = 300,  # 5 minutes
    ):
        """Initialize retry scheduler.

        Args:
            queue: The retry queue to process
            storage: Fallback storage for updating tickets
            check_interval: Seconds between queue checks
        """
        self._queue = queue
        self._storage = storage
        self._check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._logger = get_logger("fallback.scheduler")

    async def start(self) -> None:
        """Start the retry scheduler."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        self._logger.info("Retry scheduler started", extra={"check_interval": self._check_interval})

    async def stop(self) -> None:
        """Stop the retry scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._logger.info("Retry scheduler stopped")

    async def _run(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Clear expired tickets
                await self._queue.clear_expired_tickets()

                # Process retryable tickets
                retry_count = 0
                while True:
                    ticket = await self._queue.dequeue()
                    if not ticket:
                        break

                    retry_count += 1
                    await self._process_ticket(ticket)

                if retry_count > 0:
                    self._logger.info(
                        f"Processed {retry_count} tickets from retry queue",
                        extra={"processed_count": retry_count},
                    )

                # Wait before next check
                await asyncio.sleep(self._check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in retry scheduler: {e}", extra={"error": str(e)})
                await asyncio.sleep(self._check_interval)  # Wait before retrying

    async def _process_ticket(self, ticket: FallbackTicket) -> None:
        """Process a single ticket retry.

        Args:
            ticket: The ticket to retry
        """
        try:
            self._logger.info(
                "Processing ticket retry",
                extra={
                    "fallback_id": ticket.fallback_id,
                    "retry_count": ticket.retry_count,
                    "integration": ticket.integration_name,
                }
            )

            # Increment retry count
            ticket.increment_retry()

            # Update status
            ticket.status = FallbackStatus.RETRYING
            await self._storage.update_ticket(ticket)

            # Here we would attempt the actual retry logic
            # This would be implemented by the integration layer
            # For now, we'll simulate success/failure

            # Simulate retry result (would be replaced with actual integration call)
            success = ticket.retry_count < 3  # Simulate success on first 3 attempts

            if success:
                # Mark as assigned
                ticket.mark_assigned(f"ticket-{ticket.fallback_id}")
                await self._storage.update_ticket(ticket)

                self._logger.info(
                    "Ticket retry successful",
                    extra={
                        "fallback_id": ticket.fallback_id,
                        "ticket_id": f"ticket-{ticket.fallback_id}",
                    }
                )
            else:
                # Check if we should continue retrying
                if ticket.is_retryable():
                    # Re-queue for next retry
                    await self._queue.enqueue(ticket)
                else:
                    # Max retries exceeded
                    ticket.mark_failed("Max retry attempts exceeded")
                    await self._storage.update_ticket(ticket)

                    self._logger.warning(
                        "Ticket retry failed - max attempts exceeded",
                        extra={"fallback_id": ticket.fallback_id, "retry_count": ticket.retry_count},
                    )

        except Exception as e:
            self._logger.error(
                f"Failed to process ticket retry: {e}",
                extra={"fallback_id": ticket.fallback_id, "error": str(e)},
            )
            # Re-queue for next retry on error
            if ticket.is_retryable():
                await self._queue.enqueue(ticket)