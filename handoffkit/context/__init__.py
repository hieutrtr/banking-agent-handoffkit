"""HandoffKit Context Packaging Module.

Contains context packager, entity extraction, and format adapters.
"""

from handoffkit.context.entity_extractor import EntityExtractor
from handoffkit.context.metadata import MetadataCollector
from handoffkit.context.models import (
    ConversationMetadata,
    ConversationPackage,
    EntityType,
    ExtractedEntity,
)
from handoffkit.context.packager import ContextPackager, ConversationPackager

__all__ = [
    "ContextPackager",
    "ConversationPackager",
    "ConversationPackage",
    "EntityExtractor",
    "EntityType",
    "ExtractedEntity",
    "MetadataCollector",
    "ConversationMetadata",
]
