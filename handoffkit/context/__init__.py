"""HandoffKit Context Packaging Module.

Contains context packager, entity extraction, and format adapters.
"""

from handoffkit.context.entity_extractor import EntityExtractor
from handoffkit.context.metadata import MetadataCollector
from handoffkit.context.models import (
    ConversationMetadata,
    ConversationPackage,
    ConversationSummary,
    EntityType,
    ExtractedEntity,
)
from handoffkit.context.packager import ConversationPackager
from handoffkit.context.summarizer import ConversationSummarizer

__all__ = [
    "ConversationPackager",
    "ConversationPackage",
    "ConversationSummarizer",
    "ConversationSummary",
    "EntityExtractor",
    "EntityType",
    "ExtractedEntity",
    "MetadataCollector",
    "ConversationMetadata",
]
