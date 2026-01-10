"""Round-robin agent assignment for distributing handoffs evenly.

This module provides the RoundRobinAssigner class which implements a thread-safe
round-robin algorithm for distributing handoffs among available agents.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from handoffkit.utils.logging import get_logger


class AssignmentRecord:
    """Record of an agent assignment."""

    def __init__(self, agent_id: str, handoff_id: str, timestamp: datetime):
        """Initialize assignment record.

        Args:
            agent_id: The ID of the assigned agent
            handoff_id: The ID of the handoff
            timestamp: When the assignment occurred
        """
        self.agent_id = agent_id
        self.handoff_id = handoff_id
        self.timestamp = timestamp


class AssignmentHistory:
    """Thread-safe circular buffer for tracking agent assignments."""

    def __init__(self, max_size: int = 1000):
        """Initialize assignment history.

        Args:
            max_size: Maximum number of assignment records to keep
        """
        self._max_size = max_size
        self._assignments: list[AssignmentRecord] = []
        self._agent_last_assignment: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def record_assignment(self, agent_id: str, handoff_id: str) -> None:
        """Record a new agent assignment.

        Args:
            agent_id: The ID of the assigned agent
            handoff_id: The ID of the handoff
        """
        async with self._lock:
            timestamp = datetime.now(timezone.utc)
            record = AssignmentRecord(agent_id, handoff_id, timestamp)

            # Add to assignments list
            self._assignments.append(record)

            # Keep only max_size records
            if len(self._assignments) > self._max_size:
                # Remove oldest records
                removed = self._assignments[: len(self._assignments) - self._max_size]
                self._assignments = self._assignments[-self._max_size :]

                # Clean up agent_last_assignment for removed records
                for record in removed:
                    if record.agent_id in self._agent_last_assignment:
                        # Check if this was the last assignment for this agent
                        latest = max(
                            (r for r in self._assignments if r.agent_id == record.agent_id),
                            key=lambda r: r.timestamp,
                            default=None,
                        )
                        if not latest:
                            del self._agent_last_assignment[record.agent_id]

            # Update last assignment timestamp
            self._agent_last_assignment[agent_id] = timestamp

    def was_recently_assigned(self, agent_id: str, window: timedelta) -> bool:
        """Check if an agent was assigned within the given time window.

        Args:
            agent_id: The agent ID to check
            window: Time window to check against

        Returns:
            True if agent was assigned within the window
        """
        # If window is zero, agent is never recently assigned
        if window.total_seconds() == 0:
            return False

        last_assignment = self._agent_last_assignment.get(agent_id)
        if not last_assignment:
            return False

        return datetime.now(timezone.utc) - last_assignment < window

    def get_last_assignment_time(self, agent_id: str) -> Optional[datetime]:
        """Get the last assignment time for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            Last assignment timestamp or None if never assigned
        """
        return self._agent_last_assignment.get(agent_id)

    async def cleanup_old_records(self, max_age: timedelta = timedelta(hours=24)) -> int:
        """Remove assignment records older than max_age.

        Args:
            max_age: Maximum age for records to keep

        Returns:
            Number of records removed
        """
        async with self._lock:
            cutoff_time = datetime.now(timezone.utc) - max_age
            old_count = len(self._assignments)

            # Filter out old records
            self._assignments = [r for r in self._assignments if r.timestamp > cutoff_time]

            # Clean up agent_last_assignment
            current_agents = {r.agent_id for r in self._assignments}
            self._agent_last_assignment = {
                agent_id: timestamp
                for agent_id, timestamp in self._agent_last_assignment.items()
                if agent_id in current_agents
            }

            return old_count - len(self._assignments)

    @property
    def size(self) -> int:
        """Get current number of assignment records."""
        return len(self._assignments)


class RoundRobinAssigner:
    """Thread-safe round-robin agent assignment."""

    def __init__(
        self,
        rotation_window_minutes: int = 5,
        assignment_history_size: int = 1000,
    ):
        """Initialize round-robin assigner.

        Args:
            rotation_window_minutes: Minutes to wait before reassigning to same agent
            assignment_history_size: Maximum number of assignments to track
        """
        self._rotation_window = timedelta(minutes=rotation_window_minutes)
        self._assignment_history = AssignmentHistory(max_size=assignment_history_size)
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._logger = get_logger("round_robin")

    async def select_agent(
        self,
        available_agents: list[dict],
        handoff_id: str,
    ) -> Optional[dict]:
        """Select next agent using round-robin algorithm.

        Args:
            available_agents: List of available agents
            handoff_id: ID of the handoff being assigned

        Returns:
            Selected agent or None if no eligible agents
        """
        if not available_agents:
            return None

        async with self._lock:
            # Filter out recently assigned agents
            eligible_agents = []
            for agent in available_agents:
                agent_id = agent["id"]
                if not self._assignment_history.was_recently_assigned(
                    agent_id, self._rotation_window
                ):
                    eligible_agents.append(agent)

            # If all agents were recently assigned, use all available
            if not eligible_agents:
                self._logger.warning(
                    "All agents were recently assigned, using all available agents",
                    extra={
                        "agent_count": len(available_agents),
                        "rotation_window_minutes": self._rotation_window.total_seconds() / 60,
                    }
                )
                eligible_agents = available_agents

            # Find the next eligible agent in rotation
            # Start from current_index and wrap around if needed
            start_index = self._current_index % len(eligible_agents)
            selected_agent = None

            # First pass: try to find an agent not recently assigned
            for i in range(len(eligible_agents)):
                candidate_index = (start_index + i) % len(eligible_agents)
                candidate = eligible_agents[candidate_index]

                # Check if this agent was recently assigned
                if not self._assignment_history.was_recently_assigned(
                    candidate["id"], self._rotation_window
                ):
                    selected_agent = candidate
                    self._current_index = (candidate_index + 1) % len(eligible_agents)
                    break

            # Second pass: if all agents were recently assigned, use rotation anyway
            if selected_agent is None:
                selected_agent = eligible_agents[start_index]
                self._current_index = (start_index + 1) % len(eligible_agents)

            # Record assignment
            await self._assignment_history.record_assignment(
                agent_id=selected_agent["id"],
                handoff_id=handoff_id,
            )

            self._logger.info(
                "Agent selected via round-robin",
                extra={
                    "agent_id": selected_agent["id"],
                    "agent_name": selected_agent["name"],
                    "handoff_id": handoff_id,
                    "eligible_agents": len(eligible_agents),
                    "total_agents": len(available_agents),
                }
            )

            return selected_agent

    async def record_assignment(self, agent_id: str, handoff_id: str) -> None:
        """Manually record an assignment (for testing or external assignments).

        Args:
            agent_id: ID of the assigned agent
            handoff_id: ID of the handoff
        """
        await self._assignment_history.record_assignment(agent_id, handoff_id)

    def get_statistics(self) -> dict:
        """Get assignment statistics.

        Returns:
            Dictionary with assignment statistics
        """
        return {
            "total_assignments": self._assignment_history.size,
            "rotation_window_minutes": self._rotation_window.total_seconds() / 60,
            "current_rotation_index": self._current_index,
        }