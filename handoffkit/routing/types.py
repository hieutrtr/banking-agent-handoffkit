"""Types for routing system."""

from enum import Enum
from typing import Any, Optional, Union


class RuleActionType(str, Enum):
    """Types of actions that can be executed."""

    ASSIGN_TO_AGENT = "assign_to_agent"
    ASSIGN_TO_QUEUE = "assign_to_queue"
    ASSIGN_TO_DEPARTMENT = "assign_to_department"
    SET_PRIORITY = "set_priority"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    SET_CUSTOM_FIELD = "set_custom_field"
    ROUTE_TO_FALLBACK = "route_to_fallback"


class ConditionType(str, Enum):
    """Types of conditions."""

    MESSAGE_CONTENT = "message_content"
    USER_ATTRIBUTE = "user_attribute"
    CONTEXT_FIELD = "context_field"
    ENTITY = "entity"
    METADATA = "metadata"
    TIME_BASED = "time_based"
    TRIGGER = "trigger"


class Operator(str, Enum):
    """Condition operators."""

    # String operators
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCHES = "regex_matches"

    # Numeric operators
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN_RANGE = "in_range"
    NOT_IN_RANGE = "not_in_range"

    # List operators
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"

    # Boolean operators
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"

    # Existence operators
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

    # Time operators
    AFTER = "after"
    BEFORE = "before"
    BETWEEN = "between"


class TimeUnit(str, Enum):
    """Time units for time-based conditions."""

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


# Type aliases for priority
PriorityType = Union[str, int]


def validate_priority(priority: Any) -> Optional[str]:
    """Validate and normalize priority value."""
    if priority is None:
        return None

    # Convert to string
    priority_str = str(priority).upper()

    # Valid priority values
    valid_priorities = {"LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"}

    if priority_str in valid_priorities:
        return priority_str

    # Try to map numeric values
    priority_map = {
        "1": "LOW",
        "2": "MEDIUM",
        "3": "HIGH",
        "4": "URGENT",
        "5": "CRITICAL",
    }

    return priority_map.get(priority_str)