"""Fallback ticket creation and management for HandoffKit.

This module provides resilient ticket creation when primary integrations fail,
ensuring no customer request is lost even during system outages.
"""

from handoffkit.fallback.models import (
    FallbackReason,
    FallbackStatus,
    FallbackTicket,
)
from handoffkit.fallback.notifier import FallbackNotifier
from handoffkit.fallback.queue import RetryQueue, RetryScheduler
from handoffkit.fallback.storage import FallbackStorage

__all__ = [
    "FallbackTicket",
    "FallbackStatus",
    "FallbackReason",
    "FallbackStorage",
    "RetryQueue",
    "RetryScheduler",
    "FallbackNotifier",
]