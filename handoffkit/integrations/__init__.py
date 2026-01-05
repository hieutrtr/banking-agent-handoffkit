"""HandoffKit Integrations Module.

Contains helpdesk platform integrations.
"""

from handoffkit.integrations.base import BaseIntegration
from handoffkit.integrations.intercom import IntercomConfig, IntercomIntegration
from handoffkit.integrations.zendesk import ZendeskConfig, ZendeskIntegration

__all__ = [
    "BaseIntegration",
    "IntercomConfig",
    "IntercomIntegration",
    "ZendeskConfig",
    "ZendeskIntegration",
]
