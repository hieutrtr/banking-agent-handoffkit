"""Condition evaluation system for routing rules."""

import re
from abc import ABC, abstractmethod
from datetime import datetime, time, timezone
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from handoffkit.core.types import ConversationContext, HandoffDecision
from handoffkit.routing.types import ConditionType, Operator, TimeUnit
from handoffkit.utils.logging import get_logger


class Condition(BaseModel):
    """Represents a single condition in a routing rule."""

    type: ConditionType = Field(description="Type of condition")
    field: Optional[str] = Field(default=None, description="Field to check (varies by type)")
    operator: Operator = Field(description="Operator to apply")
    value: Optional[Any] = Field(default=None, description="Value to compare against")
    negate: bool = Field(default=False, description="Whether to negate the condition")
    case_sensitive: bool = Field(default=False, description="Whether string comparison is case-sensitive")

    def __init__(self, **data):
        """Initialize condition with validation."""
        super().__init__(**data)
        self._validate_condition()

    def _validate_condition(self) -> None:
        """Validate condition configuration."""
        # Type-specific validation
        if self.type == ConditionType.MESSAGE_CONTENT:
            if not self.field:
                raise ValueError("field is required for message_content conditions")
            valid_fields = {"content", "speaker", "timestamp", "length"}
            if self.field not in valid_fields:
                raise ValueError(f"Invalid field '{self.field}' for message_content. Valid fields: {valid_fields}")

        elif self.type == ConditionType.USER_ATTRIBUTE:
            if not self.field:
                raise ValueError("field is required for user_attribute conditions")

        elif self.type == ConditionType.CONTEXT_FIELD:
            if not self.field:
                raise ValueError("field is required for context_field conditions")

        elif self.type == ConditionType.ENTITY:
            if not self.field:
                raise ValueError("field is required for entity conditions")

        elif self.type == ConditionType.METADATA:
            if not self.field:
                raise ValueError("field is required for metadata conditions")

        elif self.type == ConditionType.TIME_BASED:
            if self.operator in (Operator.AFTER, Operator.BEFORE, Operator.BETWEEN):
                if self.value is None:
                    raise ValueError("value is required for time_based conditions")

        elif self.type == ConditionType.TRIGGER:
            if not self.field:
                raise ValueError("field is required for trigger conditions")

        # Operator validation
        self._validate_operator()

    def _validate_operator(self) -> None:
        """Validate operator is compatible with condition type."""
        # String operators
        if self.operator in {
            Operator.CONTAINS,
            Operator.NOT_CONTAINS,
            Operator.STARTS_WITH,
            Operator.ENDS_WITH,
            Operator.REGEX_MATCHES,
        }:
            if self.value is not None and not isinstance(self.value, str):
                raise ValueError(f"Operator {self.operator} requires string value")

        # Numeric operators
        elif self.operator in {
            Operator.GREATER_THAN,
            Operator.LESS_THAN,
            Operator.GREATER_EQUAL,
            Operator.LESS_EQUAL,
        }:
            if self.value is not None and not isinstance(self.value, (int, float)):
                raise ValueError(f"Operator {self.operator} requires numeric value")

        # List operators
        elif self.operator in {Operator.IN_LIST, Operator.NOT_IN_LIST}:
            if not isinstance(self.value, list):
                raise ValueError(f"Operator {self.operator} requires list value")

        # Boolean operators
        elif self.operator in {Operator.IS_TRUE, Operator.IS_FALSE}:
            if self.value is not None:
                raise ValueError(f"Operator {self.operator} doesn't require a value")

        # Existence operators
        elif self.operator in {Operator.EXISTS, Operator.NOT_EXISTS}:
            if self.value is not None:
                raise ValueError(f"Operator {self.operator} doesn't require a value")

    async def evaluate(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> bool:
        """Evaluate this condition against the conversation.

        Args:
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            True if condition matches, False otherwise
        """
        try:
            # Get the value to check
            actual_value = await self._extract_value(context, decision, metadata)

            # Apply the operator
            matches = self._apply_operator(actual_value, self.operator, self.value)

            # Apply negation if needed
            if self.negate:
                matches = not matches

            return matches

        except Exception as e:
            logger = get_logger("routing.conditions")
            logger.warning(
                f"Condition evaluation failed: {e}",
                extra={
                    "condition_type": self.type.value,
                    "field": self.field,
                    "operator": self.operator.value,
                    "error": str(e),
                }
            )
            # On error, condition doesn't match
            return False

    async def _extract_value(
        self,
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> Any:
        """Extract the value to check based on condition type."""
        if self.type == ConditionType.MESSAGE_CONTENT:
            return self._extract_message_value(context)

        elif self.type == ConditionType.USER_ATTRIBUTE:
            return self._extract_user_value(context, metadata)

        elif self.type == ConditionType.CONTEXT_FIELD:
            return self._extract_context_value(context, metadata)

        elif self.type == ConditionType.ENTITY:
            return self._extract_entity_value(context)

        elif self.type == ConditionType.METADATA:
            return self._extract_metadata_value(context, metadata)

        elif self.type == ConditionType.TIME_BASED:
            return self._extract_time_value()

        elif self.type == ConditionType.TRIGGER:
            return self._extract_trigger_value(decision)

        else:
            raise ValueError(f"Unsupported condition type: {self.type}")

    def _extract_message_value(self, context: ConversationContext) -> Any:
        """Extract value from message content."""
        if self.field == "content":
            # Get last user message content
            for msg in reversed(context.messages):
                if msg.speaker.value == "user":
                    return msg.content
            return ""

        elif self.field == "speaker":
            # Get speaker of last message
            if context.messages:
                return context.messages[-1].speaker.value
            return None

        elif self.field == "timestamp":
            # Get timestamp of last message
            if context.messages:
                return context.messages[-1].timestamp
            return None

        elif self.field == "length":
            # Get total conversation length
            return len(context.messages)

        else:
            raise ValueError(f"Unknown message field: {self.field}")

    def _extract_user_value(self, context: ConversationContext, metadata: dict[str, Any]) -> Any:
        """Extract user attribute value."""
        user_data = metadata.get("user", {})
        if not isinstance(user_data, dict):
            user_data = {}

        if self.field == "id":
            return context.user_id

        return user_data.get(self.field)

    def _extract_context_value(self, context: ConversationContext, metadata: dict[str, Any]) -> Any:
        """Extract context field value."""
        if self.field == "conversation_id":
            return context.conversation_id

        elif self.field == "channel":
            return metadata.get("channel")

        elif self.field == "user_id":
            return context.user_id

        else:
            # Generic metadata access
            return metadata.get(self.field)

    def _extract_entity_value(self, context: ConversationContext) -> Any:
        """Extract entity value."""
        entities = context.metadata.get("extracted_entities", [])
        if not isinstance(entities, list):
            return None

        # Find entity by type
        for entity in entities:
            if isinstance(entity, dict) and entity.get("entity_type") == self.field:
                return entity.get("value")

        return None

    def _extract_metadata_value(self, context: ConversationContext, metadata: dict[str, Any]) -> Any:
        """Extract metadata field value."""
        return context.metadata.get(self.field)

    def _extract_time_value(self) -> Any:
        """Extract time-based value."""
        if self.operator in (Operator.AFTER, Operator.BEFORE, Operator.BETWEEN):
            return datetime.now(timezone.utc)

        else:
            # For other time operators, return the value
            return self.value

    def _extract_trigger_value(self, decision: HandoffDecision) -> Any:
        """Extract trigger-related value."""
        if not decision.trigger_results:
            return None

        trigger = decision.trigger_results[0]  # Use first trigger

        if self.field == "trigger_type":
            return trigger.trigger_type

        elif self.field == "confidence":
            return trigger.confidence

        elif self.field == "reason":
            return trigger.reason

        else:
            return trigger.metadata.get(self.field)

    def _apply_operator(self, actual_value: Any, operator: Operator, expected_value: Any) -> bool:
        """Apply operator to compare values."""
        # Handle existence operators
        if operator == Operator.EXISTS:
            return actual_value is not None
        elif operator == Operator.NOT_EXISTS:
            return actual_value is None

        # Handle boolean operators
        elif operator == Operator.IS_TRUE:
            return bool(actual_value) is True
        elif operator == Operator.IS_FALSE:
            return bool(actual_value) is False

        # Handle null actual values for other operators
        if actual_value is None:
            return False

        # String operators
        if operator == Operator.EQUALS:
            if self.case_sensitive and isinstance(actual_value, str) and isinstance(expected_value, str):
                return actual_value == expected_value
            else:
                return str(actual_value).lower() == str(expected_value).lower()

        elif operator == Operator.NOT_EQUALS:
            return not self._apply_operator(actual_value, Operator.EQUALS, expected_value)

        elif operator == Operator.CONTAINS:
            return str(expected_value).lower() in str(actual_value).lower()

        elif operator == Operator.NOT_CONTAINS:
            return not self._apply_operator(actual_value, Operator.CONTAINS, expected_value)

        elif operator == Operator.STARTS_WITH:
            return str(actual_value).lower().startswith(str(expected_value).lower())

        elif operator == Operator.ENDS_WITH:
            return str(actual_value).lower().endswith(str(expected_value).lower())

        elif operator == Operator.REGEX_MATCHES:
            try:
                pattern = re.compile(str(expected_value))
                return bool(pattern.search(str(actual_value)))
            except re.error:
                return False

        # Numeric operators
        elif operator == Operator.GREATER_THAN:
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False

        elif operator == Operator.LESS_THAN:
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False

        elif operator == Operator.GREATER_EQUAL:
            try:
                return float(actual_value) >= float(expected_value)
            except (ValueError, TypeError):
                return False

        elif operator == Operator.LESS_EQUAL:
            try:
                return float(actual_value) <= float(expected_value)
            except (ValueError, TypeError):
                return False

        elif operator == Operator.IN_RANGE:
            if not isinstance(expected_value, (list, tuple)) or len(expected_value) != 2:
                return False
            try:
                min_val, max_val = float(expected_value[0]), float(expected_value[1])
                actual_val = float(actual_value)
                return min_val <= actual_val <= max_val
            except (ValueError, TypeError):
                return False

        # List operators
        elif operator == Operator.IN_LIST:
            if not isinstance(expected_value, list):
                return False
            return str(actual_value) in [str(item) for item in expected_value]

        elif operator == Operator.NOT_IN_LIST:
            return not self._apply_operator(actual_value, Operator.IN_LIST, expected_value)

        else:
            logger = get_logger("routing.conditions")
            logger.warning(f"Unknown operator: {operator}")
            return False

    def get_summary(self) -> dict[str, Any]:
        """Get condition summary."""
        return {
            "type": self.type.value,
            "field": self.field,
            "operator": self.operator.value,
            "has_value": self.value is not None,
            "negate": self.negate,
            "case_sensitive": self.case_sensitive,
        }


class ConditionEvaluator:
    """Evaluates conditions for routing rules."""

    def __init__(self):
        """Initialize condition evaluator."""
        self._logger = get_logger("routing.conditions")

    async def evaluate_conditions(
        self,
        conditions: list[dict[str, Any]],
        context: ConversationContext,
        decision: HandoffDecision,
        metadata: dict[str, Any],
    ) -> list[bool]:
        """Evaluate a list of conditions.

        Args:
            conditions: List of condition data
            context: Conversation context
            decision: Handoff decision
            metadata: Additional metadata

        Returns:
            List of evaluation results
        """
        results = []
        for condition_data in conditions:
            try:
                condition = Condition(**condition_data)
                result = await condition.evaluate(context, decision, metadata)
                results.append(result)
            except Exception as e:
                self._logger.error(
                    f"Failed to evaluate condition: {e}",
                    extra={"error": str(e), "condition_data": condition_data}
                )
                results.append(False)

        return results