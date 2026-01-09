"""HandoffKit Integrations Module.

Contains helpdesk platform integrations.
"""

from handoffkit.integrations.base import BaseIntegration
from handoffkit.integrations.generic import GenericIntegration
from handoffkit.integrations.intercom import IntercomConfig, IntercomIntegration
from handoffkit.integrations.markdown import MarkdownIntegration
from handoffkit.integrations.zendesk import ZendeskConfig, ZendeskIntegration

__all__ = [
    "BaseIntegration",
    "GenericIntegration",
    "IntercomConfig",
    "IntercomIntegration",
    "MarkdownIntegration",
    "ZendeskConfig",
    "ZendeskIntegration",
]
