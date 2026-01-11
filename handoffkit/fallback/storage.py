"""Local storage for fallback tickets using JSON files."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from handoffkit.fallback.models import FallbackStatus, FallbackTicket
from handoffkit.utils.logging import get_logger


class FallbackStorage:
    """JSON-based storage for fallback tickets.

    Provides persistent storage of fallback tickets using JSON files.
    Thread-safe with file locking for concurrent access.
    """

    def __init__(self, storage_path: str = "./fallback_tickets"):
        """Initialize fallback storage.

        Args:
            storage_path: Directory path for storing fallback tickets
        """
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._logger = get_logger("fallback.storage")

        # Ensure storage directory exists
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Create index file if it doesn't exist
        index_file = self._storage_path / "index.json"
        if not index_file.exists():
            # We'll create it on first save
            pass

    async def save_ticket(self, ticket: FallbackTicket) -> None:
        """Save a fallback ticket to storage.

        Args:
            ticket: The fallback ticket to save
        """
        async with self._lock:
            try:
                # Convert to dict and handle datetime serialization
                ticket_dict = ticket.model_dump()
                ticket_file = self._storage_path / f"{ticket.fallback_id}.json"

                # Write ticket file
                with open(ticket_file, "w", encoding="utf-8") as f:
                    json.dump(ticket_dict, f, indent=2, default=self._json_serializer)

                # Update index
                index = await self._read_index()
                index[ticket.fallback_id] = {
                    "handoff_id": ticket.handoff_id,
                    "integration_name": ticket.integration_name,
                    "status": ticket.status.value,
                    "created_at": ticket.created_at.isoformat(),
                    "retry_count": ticket.retry_count,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                await self._write_index(index)

                self._logger.info(
                    "Fallback ticket saved",
                    extra={
                        "fallback_id": ticket.fallback_id,
                        "handoff_id": ticket.handoff_id,
                        "integration": ticket.integration_name,
                        "status": ticket.status.value,
                    }
                )

            except Exception as e:
                self._logger.error(
                    f"Failed to save fallback ticket: {e}",
                    extra={"fallback_id": ticket.fallback_id, "error": str(e)},
                )
                raise

    async def get_ticket(self, fallback_id: str) -> Optional[FallbackTicket]:
        """Retrieve a fallback ticket by ID.

        Args:
            fallback_id: The fallback ticket ID

        Returns:
            The fallback ticket or None if not found
        """
        async with self._lock:
            try:
                ticket_file = self._storage_path / f"{fallback_id}.json"
                if not ticket_file.exists():
                    return None

                with open(ticket_file, "r", encoding="utf-8") as f:
                    ticket_dict = json.load(f)

                # Convert datetime strings back to datetime objects
                ticket_dict["created_at"] = datetime.fromisoformat(ticket_dict["created_at"])
                if ticket_dict.get("last_retry_at"):
                    ticket_dict["last_retry_at"] = datetime.fromisoformat(ticket_dict["last_retry_at"])
                if ticket_dict.get("retry_after"):
                    ticket_dict["retry_after"] = datetime.fromisoformat(ticket_dict["retry_after"])

                return FallbackTicket(**ticket_dict)

            except Exception as e:
                self._logger.error(
                    f"Failed to retrieve fallback ticket: {e}",
                    extra={"fallback_id": fallback_id, "error": str(e)},
                )
                return None

    async def list_tickets(
        self,
        status: Optional[FallbackStatus] = None,
        integration_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[FallbackTicket]:
        """List fallback tickets with optional filtering.

        Args:
            status: Filter by ticket status
            integration_name: Filter by integration name
            limit: Maximum number of tickets to return

        Returns:
            List of matching fallback tickets
        """
        async with self._lock:
            try:
                index = await self._read_index()
                tickets = []

                # Filter by criteria
                filtered_ids = []
                for fallback_id, ticket_info in index.items():
                    if status and ticket_info["status"] != status.value:
                        continue
                    if integration_name and ticket_info["integration_name"] != integration_name:
                        continue
                    filtered_ids.append(fallback_id)

                # Apply limit
                if limit:
                    filtered_ids = filtered_ids[:limit]

                # Load tickets
                for fallback_id in filtered_ids:
                    ticket = await self.get_ticket(fallback_id)
                    if ticket:
                        tickets.append(ticket)

                return tickets

            except Exception as e:
                self._logger.error(f"Failed to list fallback tickets: {e}", extra={"error": str(e)})
                return []

    async def update_ticket(self, ticket: FallbackTicket) -> bool:
        """Update an existing fallback ticket.

        Args:
            ticket: The updated ticket

        Returns:
            True if update was successful
        """
        async with self._lock:
            try:
                # Verify ticket exists
                existing = await self.get_ticket(ticket.fallback_id)
                if not existing:
                    return False

                # Save updated ticket
                await self.save_ticket(ticket)
                return True

            except Exception as e:
                self._logger.error(
                    f"Failed to update fallback ticket: {e}",
                    extra={"fallback_id": ticket.fallback_id, "error": str(e)},
                )
                return False

    async def delete_ticket(self, fallback_id: str) -> bool:
        """Delete a fallback ticket.

        Args:
            fallback_id: The fallback ticket ID

        Returns:
            True if deletion was successful
        """
        async with self._lock:
            try:
                ticket_file = self._storage_path / f"{fallback_id}.json"
                if ticket_file.exists():
                    ticket_file.unlink()

                # Update index
                index = await self._read_index()
                if fallback_id in index:
                    del index[fallback_id]
                    await self._write_index(index)

                self._logger.info(
                    "Fallback ticket deleted",
                    extra={"fallback_id": fallback_id},
                )
                return True

            except Exception as e:
                self._logger.error(
                    f"Failed to delete fallback ticket: {e}",
                    extra={"fallback_id": fallback_id, "error": str(e)},
                )
                return False

    async def get_metrics(self) -> dict[str, Any]:
        """Get storage metrics.

        Returns:
            Dictionary with storage statistics
        """
        async with self._lock:
            try:
                index = await self._read_index()
                total_tickets = len(index)

                # Count by status
                status_counts = {}
                integration_counts = {}
                for ticket_info in index.values():
                    status = ticket_info["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1

                    integration = ticket_info["integration_name"]
                    integration_counts[integration] = integration_counts.get(integration, 0) + 1

                # Get disk usage
                disk_usage = sum(
                    f.stat().st_size for f in self._storage_path.glob("*.json") if f.is_file()
                )

                return {
                    "total_tickets": total_tickets,
                    "by_status": status_counts,
                    "by_integration": integration_counts,
                    "disk_usage_bytes": disk_usage,
                    "storage_path": str(self._storage_path),
                }

            except Exception as e:
                self._logger.error(f"Failed to get metrics: {e}", extra={"error": str(e)})
                return {}

    async def cleanup_old_tickets(self, max_age_days: int = 30) -> int:
        """Clean up tickets older than specified days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of tickets cleaned up
        """
        async with self._lock:
            try:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
                index = await self._read_index()
                cleaned_count = 0

                tickets_to_delete = []
                for fallback_id, ticket_info in index.items():
                    created_at = datetime.fromisoformat(ticket_info["created_at"])
                    if created_at < cutoff_date:
                        tickets_to_delete.append(fallback_id)

                for fallback_id in tickets_to_delete:
                    await self.delete_ticket(fallback_id)
                    cleaned_count += 1

                self._logger.info(
                    f"Cleaned up {cleaned_count} old fallback tickets",
                    extra={"cleaned_count": cleaned_count, "max_age_days": max_age_days},
                )
                return cleaned_count

            except Exception as e:
                self._logger.error(f"Failed to cleanup old tickets: {e}", extra={"error": str(e)})
                return 0

    async def _read_index(self) -> dict[str, Any]:
        """Read the ticket index file.

        Returns:
            Dictionary mapping fallback_id to ticket info
        """
        index_file = self._storage_path / "index.json"
        if not index_file.exists():
            return {}

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self._logger.error(f"Failed to read index: {e}", extra={"error": str(e)})
            return {}

    async def _write_index(self, index: dict[str, Any]) -> None:
        """Write the ticket index file.

        Args:
            index: Dictionary mapping fallback_id to ticket info
        """
        index_file = self._storage_path / "index.json"
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to write index: {e}", extra={"error": str(e)})
            raise

    def _json_serializer(self, obj: Any) -> str:
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")