"""Trigger factory for creating and managing triggers."""

from typing import Any, Optional

from handoffkit.core.config import TriggerConfig
from handoffkit.triggers.base import BaseTrigger
from handoffkit.triggers.custom_rules import CustomRuleTrigger
from handoffkit.triggers.direct_request import DirectRequestTrigger
from handoffkit.triggers.failure_tracking import FailureTrackingTrigger
from handoffkit.triggers.keyword import KeywordTrigger


class TriggerFactory:
    """Factory for creating and managing trigger instances."""

    _registry: dict[str, type[BaseTrigger]] = {
        "direct_request": DirectRequestTrigger,
        "failure_tracking": FailureTrackingTrigger,
        "keyword": KeywordTrigger,
        "custom_rule": CustomRuleTrigger,
    }

    @classmethod
    def register(cls, name: str, trigger_class: type[BaseTrigger]) -> None:
        """Register a custom trigger type.

        Args:
            name: Name to register the trigger under.
            trigger_class: The trigger class to register.
        """
        cls._registry[name] = trigger_class

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> BaseTrigger:
        """Create a trigger instance by name.

        Args:
            name: Name of the trigger type.
            **kwargs: Arguments to pass to the trigger constructor.

        Returns:
            Configured trigger instance.

        Raises:
            ValueError: If trigger type is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown trigger type: {name}")
        return cls._registry[name](**kwargs)

    @classmethod
    def create_from_config(cls, config: TriggerConfig) -> list[BaseTrigger]:
        """Create all triggers from configuration.

        Args:
            config: Trigger configuration.

        Returns:
            List of configured trigger instances.
        """
        triggers: list[BaseTrigger] = []

        if config.direct_request_enabled:
            triggers.append(DirectRequestTrigger())

        triggers.append(FailureTrackingTrigger(failure_threshold=config.failure_threshold))

        if config.critical_keywords:
            triggers.append(KeywordTrigger(keywords=config.critical_keywords))

        if config.custom_rules_enabled:
            triggers.append(CustomRuleTrigger())

        return triggers
