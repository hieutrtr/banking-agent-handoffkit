"""Custom rule engine trigger."""

import re
import time
import uuid
from typing import Any, Optional, Union

from handoffkit.core.types import Message, TriggerResult, TriggerType
from handoffkit.triggers.base import BaseTrigger
from handoffkit.utils.logging import get_logger


# Priority order mapping (higher number = higher priority)
PRIORITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "immediate": 4,
    "urgent": 4,  # Alias for immediate
}


class CustomRuleTrigger(BaseTrigger):
    """Evaluates custom IF-THEN-priority rules for handoff.

    Rule format:
    ```
    {
        "id": "rule-id",
        "name": "Rule Name",
        "condition": {"field": "message.content", "operator": "contains", "value": "urgent"},
        "priority": "high",
        "enabled": True
    }
    ```

    Conditions support:
    - message.content contains "text"
    - message.content matches "regex"
    - context.user_tier == "premium"
    - context.order_value > 1000
    - conversation.length > 10
    - AND/OR compound conditions
    """

    @property
    def trigger_name(self) -> str:
        return "custom_rule"

    def __init__(self, rules: Optional[list[dict[str, Any]]] = None) -> None:
        """Initialize with custom rules.

        Args:
            rules: List of rule definitions.
        """
        self._rules: list[dict[str, Any]] = []
        self._logger = get_logger("trigger.custom_rule")
        self._compiled_patterns: dict[str, re.Pattern[str]] = {}

        # Add initial rules if provided
        if rules:
            for rule in rules:
                self.add_rule(rule)

    def add_rule(self, rule: dict[str, Any]) -> None:
        """Add a custom rule.

        Args:
            rule: Rule definition with condition and priority.
        """
        # Auto-generate ID if not provided
        if "id" not in rule or rule["id"] is None:
            rule["id"] = f"rule-{uuid.uuid4().hex[:8]}"

        # Ensure enabled defaults to True
        if "enabled" not in rule:
            rule["enabled"] = True

        self._rules.append(rule)

        # Pre-compile regex patterns for performance
        self._precompile_patterns(rule.get("condition", {}))

    def _precompile_patterns(self, condition: dict[str, Any]) -> None:
        """Pre-compile regex patterns in conditions.

        Args:
            condition: Condition dict to scan for regex patterns.
        """
        if not condition:
            return

        # Check for compound conditions
        if "operator" in condition and condition["operator"] in ("AND", "OR"):
            for sub_condition in condition.get("conditions", []):
                self._precompile_patterns(sub_condition)
            return

        # Check for matches operator
        if condition.get("operator") == "matches":
            pattern = condition.get("value", "")
            if pattern and pattern not in self._compiled_patterns:
                try:
                    self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    self._logger.warning(f"Invalid regex pattern: {pattern}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID.

        Args:
            rule_id: Identifier of the rule to remove.

        Returns:
            True if rule was found and removed.
        """
        for i, rule in enumerate(self._rules):
            if rule.get("id") == rule_id:
                self._rules.pop(i)
                return True
        return False

    def get_rules(self) -> list[dict[str, Any]]:
        """Get all configured rules.

        Returns:
            List of rule definitions.
        """
        return self._rules.copy()

    def _get_field_value(
        self,
        field: str,
        message: Message,
        history: Optional[list[Message]],
        context: Optional[dict[str, Any]],
    ) -> Any:
        """Get the value of a field for condition evaluation.

        Args:
            field: Field path like "message.content" or "context.user_tier"
            message: Current message
            history: Conversation history
            context: Additional context

        Returns:
            The field value or None if not found.
        """
        parts = field.split(".", 1)
        if len(parts) != 2:
            return None

        category, key = parts

        if category == "message":
            if key == "content":
                return message.content
            elif key == "speaker":
                return message.speaker.value if hasattr(message.speaker, "value") else str(message.speaker)
            return None

        elif category == "context":
            if context is None:
                return None
            return context.get(key)

        elif category == "conversation":
            if key == "length":
                return len(history) if history else 0
            return None

        return None

    def _evaluate_simple_condition(
        self,
        condition: dict[str, Any],
        message: Message,
        history: Optional[list[Message]],
        context: Optional[dict[str, Any]],
    ) -> bool:
        """Evaluate a simple (non-compound) condition.

        Args:
            condition: Condition with field, operator, value
            message: Current message
            history: Conversation history
            context: Additional context

        Returns:
            True if condition matches.
        """
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        expected_value = condition.get("value")

        actual_value = self._get_field_value(field, message, history, context)

        # Handle missing values gracefully
        if actual_value is None:
            return False

        try:
            if operator == "contains":
                # Case-insensitive string contains
                return str(expected_value).lower() in str(actual_value).lower()

            elif operator == "matches":
                # Regex match
                pattern = self._compiled_patterns.get(expected_value)
                if pattern:
                    return bool(pattern.search(str(actual_value)))
                # Fallback to uncompiled pattern
                return bool(re.search(expected_value, str(actual_value), re.IGNORECASE))

            elif operator == "==":
                return actual_value == expected_value

            elif operator == "!=":
                return actual_value != expected_value

            elif operator == "<":
                return float(actual_value) < float(expected_value)

            elif operator == ">":
                return float(actual_value) > float(expected_value)

            elif operator == "<=":
                return float(actual_value) <= float(expected_value)

            elif operator == ">=":
                return float(actual_value) >= float(expected_value)

            else:
                self._logger.warning(f"Unknown operator: {operator}")
                return False

        except (ValueError, TypeError) as e:
            self._logger.debug(f"Condition evaluation error: {e}")
            return False

    def _evaluate_condition(
        self,
        condition: dict[str, Any],
        message: Message,
        history: Optional[list[Message]],
        context: Optional[dict[str, Any]],
    ) -> bool:
        """Evaluate a condition (simple or compound).

        Args:
            condition: Condition dict
            message: Current message
            history: Conversation history
            context: Additional context

        Returns:
            True if condition matches.
        """
        if not condition:
            return False

        # Check for compound conditions
        operator = condition.get("operator", "")
        if operator in ("AND", "OR"):
            sub_conditions = condition.get("conditions", [])
            if not sub_conditions:
                return False

            if operator == "AND":
                return all(
                    self._evaluate_condition(sub, message, history, context)
                    for sub in sub_conditions
                )
            else:  # OR
                return any(
                    self._evaluate_condition(sub, message, history, context)
                    for sub in sub_conditions
                )

        # Simple condition
        return self._evaluate_simple_condition(condition, message, history, context)

    async def evaluate(
        self,
        message: Message,
        history: Optional[list[Message]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> TriggerResult:
        """Evaluate message against custom rules.

        Args:
            message: The current message to evaluate.
            history: Previous messages in the conversation.
            context: Additional context for evaluation.

        Returns:
            TriggerResult indicating if a custom rule matched.
        """
        start_time = time.perf_counter()

        # Log evaluation start
        message_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
        self._logger.debug(
            "Evaluating custom rule trigger",
            extra={
                "message_preview": message_preview,
                "trigger_type": "custom_rule",
                "rule_count": len(self._rules),
            },
        )

        # No rules configured
        if not self._rules:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._logger.debug(
                "Custom rule trigger - no rules configured",
                extra={
                    "triggered": False,
                    "duration_ms": round(duration_ms, 2),
                    "trigger_type": "custom_rule",
                },
            )
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                reason=None,
                metadata={"duration_ms": round(duration_ms, 2)},
            )

        # Evaluate all rules and collect matches
        matching_rules: list[dict[str, Any]] = []

        for rule in self._rules:
            # Skip disabled rules
            if not rule.get("enabled", True):
                continue

            condition = rule.get("condition", {})
            if self._evaluate_condition(condition, message, history, context):
                matching_rules.append(rule)
                self._logger.debug(
                    f"Custom rule trigger - rule matched: {rule.get('id')}",
                    extra={
                        "rule_id": rule.get("id"),
                        "rule_name": rule.get("name"),
                        "priority": rule.get("priority"),
                        "trigger_type": "custom_rule",
                    },
                )

        duration_ms = (time.perf_counter() - start_time) * 1000

        # No matching rules
        if not matching_rules:
            self._logger.debug(
                "Custom rule trigger - no rules matched",
                extra={
                    "triggered": False,
                    "duration_ms": round(duration_ms, 2),
                    "trigger_type": "custom_rule",
                },
            )
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                reason=None,
                metadata={"duration_ms": round(duration_ms, 2)},
            )

        # Select highest priority matching rule
        matching_rules.sort(
            key=lambda r: PRIORITY_ORDER.get(r.get("priority", "low"), 0),
            reverse=True,
        )
        winner = matching_rules[0]

        # Log all matching rules for debugging
        self._logger.debug(
            "Custom rule trigger - triggered",
            extra={
                "triggered": True,
                "matched_rule_id": winner.get("id"),
                "matched_rule_name": winner.get("name"),
                "priority": winner.get("priority"),
                "all_matching_rules": [r.get("id") for r in matching_rules],
                "duration_ms": round(duration_ms, 2),
                "trigger_type": "custom_rule",
            },
        )

        return TriggerResult(
            triggered=True,
            trigger_type=TriggerType.CUSTOM_RULE,
            confidence=0.9,
            reason=f"Matched custom rule: '{winner.get('name')}' (id: {winner.get('id')})",
            metadata={
                "duration_ms": round(duration_ms, 2),
                "matched_rule_id": winner.get("id"),
                "matched_rule_name": winner.get("name"),
                "priority": winner.get("priority"),
                "matched_rules": [
                    {"id": r.get("id"), "name": r.get("name"), "priority": r.get("priority")}
                    for r in matching_rules
                ],
            },
        )
