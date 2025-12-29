"""Context format adapters for different output formats."""

from handoffkit.context.adapters.base import BaseAdapter
from handoffkit.context.adapters.json_adapter import JSONAdapter
from handoffkit.context.adapters.markdown_adapter import MarkdownAdapter

__all__ = [
    "BaseAdapter",
    "JSONAdapter",
    "MarkdownAdapter",
]
