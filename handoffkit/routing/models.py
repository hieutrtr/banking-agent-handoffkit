"""Data models for routing rules."""

from datetime import datetime, timezone
from typing import Any, Optional, Union, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from handoffkit.routing.types import RuleActionType, ConditionType, Operator

if TYPE_CHECKING:
    from handoffkit.core.types import HandoffPriority
else:
    HandoffPriority = None


class RuleMetadata(BaseModel):
    """Metadata for routing rules."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(default=None, description="Who created the rule")
    description: Optional[str] = Field(default=None, description="Rule description")
    tags: list[str] = Field(default_factory=list, description="Rule tags")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    version: int = Field(default=1, ge=1, description="Rule version")

    def bump_version(self) -> None:
        """Increment version and update timestamp."""
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)


class RuleAction(BaseModel):
    """Represents an action to take when a rule matches."""

    type: str = Field(description="Action type")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")

    @field_validator("type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Validate action type."""
        # Use the enum values for validation
        valid_types = {action_type.value for action_type in RuleActionType}
        if v not in valid_types:
            raise ValueError(f"Invalid action type: {v}")
        return v

    def get_agent_id(self) -> Optional[str]:
        """Get agent ID for assign_to_agent action."""
        if self.type == "assign_to_agent":
            return self.parameters.get("agent_id")
        return None

    def get_queue_name(self) -> Optional[str]:
        """Get queue name for assign_to_queue action."""
        if self.type == "assign_to_queue":
            return self.parameters.get("queue_name")
        return None

    def get_department(self) -> Optional[str]:
        """Get department for assign_to_department action."""
        if self.type == "assign_to_department":
            return self.parameters.get("department")
        return None

    def get_priority(self) -> Optional[str]:
        """Get priority for set_priority action."""
        if self.type == "set_priority":
            from handoffkit.routing.types import validate_priority
            priority_value = self.parameters.get("priority")
            return validate_priority(priority_value)
        return None

    def get_tags(self) -> list[str]:
        """Get tags for add_tags/remove_tags action."""
        if self.type in ("add_tags", "remove_tags"):
            tags = self.parameters.get("tags", [])
            if isinstance(tags, list):
                return tags
        return []

    def get_custom_field(self) -> tuple[str, Any]:
        """Get custom field for set_custom_field action."""
        if self.type == "set_custom_field":
            field_name = self.parameters.get("field_name")
            field_value = self.parameters.get("field_value")
            if field_name is not None:
                return field_name, field_value
        return "", None


class RoutingRule(BaseModel):
    """Represents a routing rule with conditions and actions."""

    name: str = Field(description="Rule name (must be unique)")
    priority: int = Field(default=100, ge=1, le=1000, description="Rule priority (1-1000, higher = earlier)")
    conditions: list[dict[str, Any]] = Field(description="List of conditions that must all match")
    actions: list[RuleAction] = Field(description="Actions to take when rule matches")
    metadata: RuleMetadata = Field(default_factory=RuleMetadata)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate rule name."""
        if not v or not v.strip():
            raise ValueError("Rule name cannot be empty")
        if len(v) > 100:
            raise ValueError("Rule name cannot exceed 100 characters")
        return v.strip()

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate conditions list."""
        if not v:
            raise ValueError("At least one condition is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 conditions per rule")
        return v

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[RuleAction]) -> list[RuleAction]:
        """Validate actions list."""
        if not v:
            raise ValueError("At least one action is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 actions per rule")
        return v

    def is_enabled(self) -> bool:
        """Check if rule is enabled."""
        return self.metadata.enabled

    def disable(self) -> None:
        """Disable the rule."""
        self.metadata.enabled = False
        self.metadata.bump_version()

    def enable(self) -> None:
        """Enable the rule."""
        self.metadata.enabled = True
        self.metadata.bump_version()

    def get_summary(self) -> dict[str, Any]:
        """Get rule summary for display."""
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.is_enabled(),
            "condition_count": len(self.conditions),
            "action_count": len(self.actions),
            "created_at": self.metadata.created_at.isoformat(),
            "updated_at": self.metadata.updated_at.isoformat(),
            "version": self.metadata.version,
        }


class RoutingResult(BaseModel):
    """Result of routing rule evaluation."""

    rule_name: str = Field(description="Name of the matching rule")
    actions_applied: list[RuleAction] = Field(description="Actions that were applied")
    routing_decision: str = Field(description="Final routing decision")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    execution_time_ms: float = Field(description="Time taken to evaluate rules")
    fallback_used: bool = Field(default=False, description="Whether fallback was used")

    def get_assigned_agent(self) -> Optional[str]:
        """Get assigned agent ID if any."""
        for action in self.actions_applied:
            if action.type == "assign_to_agent":
                return action.get_agent_id()
        return None

    def get_assigned_queue(self) -> Optional[str]:
        """Get assigned queue if any."""
        for action in self.actions_applied:
            if action.type == "assign_to_queue":
                return action.get_queue_name()
        return None

    def get_assigned_department(self) -> Optional[str]:
        """Get assigned department if any."""
        for action in self.actions_applied:
            if action.type == "assign_to_department":
                return action.get_department()
        return None

    def get_priority(self) -> Optional[str]:
        """Get assigned priority if any."""
        for action in self.actions_applied:
            if action.type == "set_priority":
                return action.get_priority()
        return None

    def get_tags(self) -> list[str]:
        """Get all tags to add."""
        tags = []
        for action in self.actions_applied:
            if action.type == "add_tags":
                tags.extend(action.get_tags())
        return tags


class RoutingConfig(BaseModel):
    """Configuration for routing rules."""

    rules: list[RoutingRule] = Field(default_factory=list, description="List of routing rules")
    default_action: str = Field(default="round_robin", description="Default action when no rules match")
    max_evaluation_time_ms: int = Field(default=100, ge=10, le=1000, description="Maximum time for rule evaluation")
    enable_caching: bool = Field(default=True, description="Enable rule evaluation caching")
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600, description="Cache TTL in seconds")
    log_evaluations: bool = Field(default=False, description="Log rule evaluations")

    @field_validator("rules")
    @classmethod
    def validate_rule_names(cls, v: list[RoutingRule]) -> list[RoutingRule]:
        """Validate that rule names are unique."""
        names = [rule.name for rule in v]
        if len(names) != len(set(names)):
            raise ValueError("Rule names must be unique")
        return v

    def get_rule(self, name: str) -> Optional[RoutingRule]:
        """Get rule by name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a new rule."""
        # Check for duplicate name
        if self.get_rule(rule.name) is not None:
            raise ValueError(f"Rule with name '{rule.name}' already exists")

        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        initial_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.name != name]
        return len(self.rules) < initial_count

    def update_rule(self, name: str, rule: RoutingRule) -> bool:
        """Update an existing rule."""
        for i, existing_rule in enumerate(self.rules):
            if existing_rule.name == name:
                # Preserve metadata
                rule.metadata = existing_rule.metadata
                rule.metadata.bump_version()
                self.rules[i] = rule
                # Re-sort by priority
                self.rules.sort(key=lambda r: r.priority, reverse=True)
                return True
        return False

    def get_enabled_rules(self) -> list[RoutingRule]:
        """Get only enabled rules, sorted by priority."""
        return [rule for rule in self.rules if rule.is_enabled()]

    def get_summary(self) -> dict[str, Any]:
        """Get configuration summary."""
        enabled_rules = self.get_enabled_rules()
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled_rules),
            "default_action": self.default_action,
            "max_evaluation_time_ms": self.max_evaluation_time_ms,
            "enable_caching": self.enable_caching,
            "rule_names": [rule.name for rule in self.rules],
        }