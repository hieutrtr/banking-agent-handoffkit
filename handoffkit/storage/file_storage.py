"""File-based storage for handoff results."""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HandoffRecord(BaseModel):
    """Record of a handoff stored in persistence."""

    handoff_id: str
    conversation_id: str
    user_id: str
    priority: str
    status: str
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    assigned_agent: Optional[str] = None
    assigned_queue: Optional[str] = None
    routing_rule: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for JSON serialization."""
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandoffRecord":
        """Create record from dictionary."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class HandoffStorage:
    """Abstract base class for handoff storage."""

    async def save(self, handoff_id: str, data: Dict[str, Any]) -> None:
        """Save handoff data."""
        raise NotImplementedError

    async def get(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """Get handoff data by ID."""
        raise NotImplementedError

    async def update_status(
        self,
        handoff_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update handoff status."""
        raise NotImplementedError

    async def list_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List handoffs for a conversation."""
        raise NotImplementedError

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all handoffs with pagination."""
        raise NotImplementedError


class FileHandoffStorage(HandoffStorage):
    """File-based storage for handoff results.

    Uses JSON files for persistence. Suitable for development and small deployments.
    For production, consider using a database-backed storage implementation.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize file-based storage.

        Args:
            storage_dir: Directory for storing handoff files. Defaults to ~/.handoffkit/data
        """
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".handoffkit", "data")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Index file for quick lookups by handoff_id
        self.index_file = self.storage_dir / "handoffs_index.json"

        # Lock for concurrent access
        self._lock = asyncio.Lock()

        # Initialize index
        self._init_index()

    def _init_index(self) -> None:
        """Initialize the handoff index file."""
        if not self.index_file.exists():
            self._save_index({})

    def _get_index(self) -> Dict[str, str]:
        """Load the handoff index."""
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_index(self, index: Dict[str, str]) -> None:
        """Save the handoff index."""
        with open(self.index_file, "w") as f:
            json.dump(index, f, indent=2)

    def _get_handoff_file(self, handoff_id: str) -> Path:
        """Get the file path for a handoff."""
        return self.storage_dir / f"{handoff_id}.json"

    async def save(self, handoff_id: str, data: Dict[str, Any]) -> None:
        """Save handoff data to storage.

        Args:
            handoff_id: Unique handoff identifier
            data: Handoff data to save
        """
        async with self._lock:
            try:
                # Create record
                record = HandoffRecord(
                    handoff_id=handoff_id,
                    conversation_id=data.get("conversation_id", ""),
                    user_id=data.get("user_id", ""),
                    priority=data.get("priority", "MEDIUM"),
                    status=data.get("status", "pending"),
                    ticket_id=data.get("ticket_id"),
                    ticket_url=data.get("ticket_url"),
                    assigned_agent=data.get("assigned_agent"),
                    assigned_queue=data.get("assigned_queue"),
                    routing_rule=data.get("routing_rule"),
                    metadata=data.get("metadata", {}),
                    history=data.get("history", [
                        {
                            "status": data.get("status", "pending"),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    ])
                )

                # Save handoff file
                handoff_file = self._get_handoff_file(handoff_id)
                with open(handoff_file, "w") as f:
                    json.dump(record.to_dict(), f, indent=2)

                # Update index
                index = self._get_index()
                index[handoff_id] = str(handoff_file)
                self._save_index(index)

                logger.info(f"Saved handoff {handoff_id} to storage")

            except Exception as e:
                logger.error(f"Failed to save handoff {handoff_id}: {e}")
                raise

    async def get(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """Get handoff data by ID.

        Args:
            handoff_id: Handoff identifier

        Returns:
            Handoff data or None if not found
        """
        async with self._lock:
            try:
                handoff_file = self._get_handoff_file(handoff_id)

                if not handoff_file.exists():
                    logger.debug(f"Handoff {handoff_id} not found in storage")
                    return None

                with open(handoff_file, "r") as f:
                    data = json.load(f)

                return data

            except Exception as e:
                logger.error(f"Failed to get handoff {handoff_id}: {e}")
                raise

    async def update_status(
        self,
        handoff_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update handoff status.

        Args:
            handoff_id: Handoff identifier
            status: New status
            metadata: Optional additional metadata

        Returns:
            True if updated successfully, False if not found
        """
        async with self._lock:
            try:
                # Get current handoff
                handoff_file = self._get_handoff_file(handoff_id)

                if not handoff_file.exists():
                    return False

                with open(handoff_file, "r") as f:
                    data = json.load(f)

                # Update status
                data["status"] = status
                data["updated_at"] = datetime.now(timezone.utc).isoformat()

                # Add to history
                if "history" not in data:
                    data["history"] = []

                data["history"].append({
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                # Update metadata if provided
                if metadata:
                    if "metadata" not in data:
                        data["metadata"] = {}
                    data["metadata"].update(metadata)

                # Save updated handoff
                with open(handoff_file, "w") as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Updated handoff {handoff_id} status to {status}")
                return True

            except Exception as e:
                logger.error(f"Failed to update handoff {handoff_id}: {e}")
                raise

    async def list_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List handoffs for a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of results

        Returns:
            List of handoff data dictionaries
        """
        results = []

        try:
            index = self._get_index()

            for handoff_id, file_path in index.items():
                handoff_file = Path(file_path)

                if not handoff_file.exists():
                    continue

                with open(handoff_file, "r") as f:
                    data = json.load(f)

                if data.get("conversation_id") == conversation_id:
                    results.append(data)

                if len(results) >= limit:
                    break

        except Exception as e:
            logger.error(f"Failed to list handoffs for conversation {conversation_id}: {e}")

        return results[:limit]

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all handoffs with pagination.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of handoff data dictionaries
        """
        results = []

        try:
            index = self._get_index()

            # Get sorted handoff IDs
            handoff_ids = sorted(index.keys())

            # Apply pagination
            for handoff_id in handoff_ids[offset:offset + limit]:
                file_path = index[handoff_id]
                handoff_file = Path(file_path)

                if not handoff_file.exists():
                    continue

                with open(handoff_file, "r") as f:
                    data = json.load(f)

                results.append(data)

        except Exception as e:
            logger.error(f"Failed to list handoffs: {e}")

        return results

    async def delete(self, handoff_id: str) -> bool:
        """Delete a handoff from storage.

        Args:
            handoff_id: Handoff identifier

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            try:
                handoff_file = self._get_handoff_file(handoff_id)

                if not handoff_file.exists():
                    return False

                # Delete file
                handoff_file.unlink()

                # Update index
                index = self._get_index()
                if handoff_id in index:
                    del index[handoff_id]
                    self._save_index(index)

                logger.info(f"Deleted handoff {handoff_id} from storage")
                return True

            except Exception as e:
                logger.error(f"Failed to delete handoff {handoff_id}: {e}")
                raise

    async def count(self) -> int:
        """Get total count of handoffs.

        Returns:
            Total number of handoffs in storage
        """
        try:
            index = self._get_index()
            return len(index)
        except Exception as e:
            logger.error(f"Failed to count handoffs: {e}")
            return 0


# Global storage instance (lazy initialization)
_storage_instance: Optional[FileHandoffStorage] = None


def get_handoff_storage() -> FileHandoffStorage:
    """Get the global handoff storage instance.

    Returns:
        FileHandoffStorage instance
    """
    global _storage_instance

    if _storage_instance is None:
        _storage_instance = FileHandoffStorage()

    return _storage_instance


async def init_handoff_storage(storage_dir: Optional[str] = None) -> FileHandoffStorage:
    """Initialize the handoff storage.

    Args:
        storage_dir: Optional custom storage directory

    Returns:
        Initialized FileHandoffStorage instance
    """
    global _storage_instance

    _storage_instance = FileHandoffStorage(storage_dir)
    logger.info(f"Initialized handoff storage at {_instance.storage_dir}")

    return _storage_instance
