"""HandoffKit Context Packaging Module.

Contains context packager and format adapters.
"""

from handoffkit.context.metadata import MetadataCollector
from handoffkit.context.models import ConversationMetadata, ConversationPackage
from handoffkit.context.packager import ContextPackager, ConversationPackager

__all__ = [
    "ContextPackager",
    "ConversationPackager",
    "ConversationPackage",
    "MetadataCollector",
    "ConversationMetadata",
]
