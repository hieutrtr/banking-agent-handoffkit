"""Handoff storage module for persisting handoff results."""

from handoffkit.storage.file_storage import FileHandoffStorage, get_handoff_storage

__all__ = [
    "FileHandoffStorage",
    "get_handoff_storage",
]