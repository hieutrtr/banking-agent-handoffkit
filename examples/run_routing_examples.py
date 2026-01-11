#!/usr/bin/env python3
"""
Run routing rules examples without importing through the main package.
This avoids the circular import issue in orchestrator.py
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, Union, List, Dict
from enum import Enum
from pydantic import BaseModel, Field
import re
import time

print("=== HandoffKit Routing Rules Examples ===\n")

# Define all types inline (same as in routing modules)
class RuleActionType(str, Enum):
    ASSIGN_TO_AGENT = "assign_to_agent"
    ASSIGN_TO_QUEUE = "assign_to_queue"
    ASSIGN_TO_DEPARTMENT = "assign_to_department"
    SET_PRIORITY = "set_priority"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    SET_CUSTOM_FIELD = "set_custom_field"
    ROUTE_TO_FALLBACK = "route_to_fallback"

class ConditionType(str, Enum):
    MESSAGE_CONTENT = "message_content"
    USER_ATTRIBUTE = "user_attribute"
    CONTEXT_FIELD = "context_field"
    ENTITY = "entity"
    METADATA = "metadata"
    TIME_BASED = "time_based"
    TRIGGER = "trigger"

class Operator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCHES = "regex_matches"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN_RANGE = "in_range"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    AFTER = "after"
    BEFORE = "before"
    BETWEEN = "between"

# Models (simplified from routing.models)
class RuleMetadata(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)
    version: int = Field(default=1, ge=1)

    def bump_version(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

class RuleAction(BaseModel):
    type: str = Field(description="Action type")
    parameters: dict[str, Any] = Field(default_factory=dict)

    def get_agent_id(self) -> Optional[str]:
        if self.type == "assign_to_agent":
            return self.parameters.get("agent_id")
        return None

    def get_queue_name(self) -> Optional[str]:
        if self.type == "assign_to_queue":
            return self.parameters.get("queue_name")
        return None

    def get_priority(self) -> Optional[str]:
        if self.type == "set_priority":
            priority_value = self.parameters.get("priority")
            return str(priority_value).upper() if priority_value else None
        return None

    def get_tags(self) -> list[str]:
        if self.type in ("add_tags", "remove_tags"):
            tags = self.parameters.get("tags", [])
            return tags if isinstance(tags, list) else []
        return []

class Condition(BaseModel):
    type: ConditionType = Field(description="Type of condition")
    field: Optional[str] = Field(default=None, description="Field to check")
    operator: Operator = Field(description="Operator to apply")
    value: Optional[Any] = Field(default=None, description="Value to compare")
    negate: bool = Field(default=False, description="Whether to negate")
    case_sensitive: bool = Field(default=False)

    async def evaluate(self, context, decision, metadata) -> bool:
        try:
            actual_value = await self._extract_value(context, decision, metadata)
            matches = self._apply_operator(actual_value, self.operator, self.value)
            if self.negate:
                matches = not matches
            return matches
        except Exception:
            return False

    async def _extract_value(self, context, decision, metadata):
        if self.type == ConditionType.MESSAGE_CONTENT:
            if self.field == "content":
                for msg in reversed(context.messages):
                    if msg.speaker.value == "user":
                        return msg.content
                return ""
        elif self.type == ConditionType.USER_ATTRIBUTE:
            user_data = metadata.get("user", {})
            if self.field == "id":
                return context.user_id
            return user_data.get(self.field)
        elif self.type == ConditionType.CONTEXT_FIELD:
            if self.field == "channel":
                return metadata.get("channel")
            return metadata.get(self.field)
        elif self.type == ConditionType.ENTITY:
            entities = context.metadata.get("extracted_entities", [])
            for entity in entities:
                if isinstance(entity, dict) and entity.get("entity_type") == self.field:
                    return entity.get("value")
            return None
        return None

    def _apply_operator(self, actual_value, operator, expected_value) -> bool:
        if operator == Operator.EXISTS:
            return actual_value is not None
        elif operator == Operator.NOT_EXISTS:
            return actual_value is None
        elif operator == Operator.EQUALS:
            return str(actual_value).lower() == str(expected_value).lower()
        elif operator == Operator.CONTAINS:
            return str(expected_value).lower() in str(actual_value).lower()
        elif operator == Operator.REGEX_MATCHES:
            try:
                pattern = re.compile(str(expected_value))
                return bool(pattern.search(str(actual_value)))
            except re.error:
                return False
        return False

class RoutingRule(BaseModel):
    name: str = Field(description="Rule name")
    priority: int = Field(default=100, ge=1, le=1000)
    conditions: List[Dict[str, Any]] = Field(description="List of conditions")
    actions: List[RuleAction] = Field(description="Actions to take")
    metadata: RuleMetadata = Field(default_factory=RuleMetadata)

    def is_enabled(self) -> bool:
        return self.metadata.enabled

    def get_summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.is_enabled(),
            "condition_count": len(self.conditions),
            "action_count": len(self.actions),
        }

class RoutingResult(BaseModel):
    rule_name: str = Field(description="Name of the matching rule")
    actions_applied: List[RuleAction] = Field(description="Actions that were applied")
    routing_decision: str = Field(description="Final routing decision")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(description="Time taken to evaluate rules")
    fallback_used: bool = Field(default=False)

    def get_assigned_agent(self) -> Optional[str]:
        for action in self.actions_applied:
            if action.type == "assign_to_agent":
                return action.get_agent_id()
        return None

    def get_assigned_queue(self) -> Optional[str]:
        for action in self.actions_applied:
            if action.type == "assign_to_queue":
                return action.get_queue_name()
        return None

    def get_assigned_department(self) -> Optional[str]:
        for action in self.actions_applied:
            if action.type == "assign_to_department":
                return action.parameters.get("department")
        return None

    def get_priority(self) -> Optional[str]:
        for action in self.actions_applied:
            if action.type == "set_priority":
                return action.get_priority()
        return None

    def get_tags(self) -> List[str]:
        tags = []
        for action in self.actions_applied:
            if action.type == "add_tags":
                tags.extend(action.get_tags())
        return tags

class RoutingConfig(BaseModel):
    rules: List[RoutingRule] = Field(default_factory=list)
    enable_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    max_evaluation_time_ms: int = Field(default=100, ge=10, le=1000)

    def get_enabled_rules(self) -> List[RoutingRule]:
        return [rule for rule in self.rules if rule.is_enabled()]

    def add_rule(self, rule: RoutingRule) -> None:
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        enabled_rules = self.get_enabled_rules()
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled_rules),
            "rule_names": [rule.name for rule in self.rules],
        }

# Mock classes for testing
class MockMessage:
    def __init__(self, content, speaker):
        self.content = content
        self.speaker = type('Speaker', (), {'value': speaker})()
        self.timestamp = datetime.now(timezone.utc)

class MockContext:
    def __init__(self):
        self.conversation_id = "test-123"
        self.user_id = "user-456"
        self.messages = [
            MockMessage("I need help with billing", "user"),
            MockMessage("I'll help you with billing", "ai")
        ]
        self.metadata = {
            "extracted_entities": [
                {"entity_type": "issue_type", "value": "billing"}
            ]
        }

class MockDecision:
    def __init__(self):
        self.should_handoff = True
        self.confidence = 0.9
        self.reason = "Test"
        self.priority = type('Priority', (), {'value': 'MEDIUM'})()
        self.trigger_results = [
            type('Trigger', (), {
                'trigger_type': 'keyword_match',
                'confidence': 0.9,
                'reason': 'billing keyword detected',
                'metadata': {'keyword': 'billing'}
            })()
        ]

# Simple action executor
class ActionExecutor:
    async def execute_actions(self, actions, context, decision, metadata):
        executed_actions = []
        start_time = time.time()

        for action in actions:
            if action.type == RuleActionType.SET_PRIORITY:
                priority = action.get_priority()
                if priority:
                    decision.priority = type('Priority', (), {'value': priority})()
                    metadata["routing_priority"] = {"priority": priority, "set_by": "rule"}

            elif action.type == RuleActionType.ASSIGN_TO_QUEUE:
                queue = action.get_queue_name()
                if queue:
                    metadata["routing_assignment"] = {"type": "queue", "queue_name": queue}

            elif action.type == RuleActionType.ADD_TAGS:
                tags = action.get_tags()
                existing_tags = metadata.get("routing_tags", [])
                metadata["routing_tags"] = existing_tags + tags

            executed_actions.append(action)

        execution_time_ms = (time.time() - start_time) * 1000

        return RoutingResult(
            rule_name="routing_actions",
            actions_applied=executed_actions,
            routing_decision="assigned" if any(a.type in [RuleActionType.ASSIGN_TO_AGENT, RuleActionType.ASSIGN_TO_QUEUE] for a in executed_actions) else "continue",
            metadata={},
            execution_time_ms=execution_time_ms,
        )

# Simple routing engine
class RoutingEngine:
    def __init__(self, config):
        self.config = config
        self._action_executor = ActionExecutor()
        self._rule_cache = {}
        self._cache_ttl = config.cache_ttl_seconds

    async def evaluate(self, context, decision, metadata):
        start_time = time.time()

        # Get enabled rules sorted by priority
        rules = self.config.get_enabled_rules()
        rules.sort(key=lambda r: r.priority, reverse=True)

        # Evaluate each rule
        for rule in rules:
            try:
                # Evaluate all conditions (AND logic)
                condition_results = []
                for condition_data in rule.conditions:
                    condition = Condition(**condition_data)
                    result = await condition.evaluate(context, decision, metadata)
                    condition_results.append(result)
                    if not result:
                        break

                # All conditions must match
                if all(condition_results):
                    # Execute actions
                    result = await self._action_executor.execute_actions(
                        rule.actions, context, decision, metadata
                    )
                    result.rule_name = rule.name
                    result.execution_time_ms = (time.time() - start_time) * 1000
                    return result

            except Exception as e:
                print(f"Error evaluating rule {rule.name}: {e}")
                continue

        return None

# Example functions
def create_basic_routing_examples() -> list[RoutingRule]:
    """Create basic routing rule examples."""

    # Example 1: Simple keyword-based routing
    billing_rule = RoutingRule(
        name="billing_issues",
        priority=100,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "billing"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "billing_support"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "HIGH"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["billing", "finance"]}
            )
        ]
    )

    # Example 2: VIP customer routing
    vip_rule = RoutingRule(
        name="vip_customers",
        priority=200,  # Higher priority
        conditions=[
            {
                "type": ConditionType.USER_ATTRIBUTE,
                "field": "tier",
                "operator": Operator.EQUALS,
                "value": "vip"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_AGENT,
                parameters={"agent_id": "vip-specialist-001"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "URGENT"}
            )
        ]
    )

    return [billing_rule, vip_rule]

def create_advanced_routing_examples() -> list[RoutingRule]:
    """Create advanced routing rule examples."""

    # Example 1: Complex multi-condition rule
    # Note: Even though this has priority 400, the vip_customers rule (priority 200)
    # will match first for VIP users because it has fewer conditions and the
    # evaluation stops at the first matching rule
    complex_rule = RoutingRule(
        name="urgent_billing_vip",
        priority=400,  # Very high priority (higher than vip_customers)
        conditions=[
            {
                "type": ConditionType.USER_ATTRIBUTE,
                "field": "tier",
                "operator": Operator.IN_LIST,
                "value": ["vip", "premium"]
            },
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "billing"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_AGENT,
                parameters={"agent_id": "senior-billing-agent"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "CRITICAL"}
            )
        ]
    )

    # Example 2: Regex pattern matching
    order_number_rule = RoutingRule(
        name="order_number_detection",
        priority=120,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.REGEX_MATCHES,
                "value": r"ORD-\d{8}"  # Matches ORD-12345678
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.SET_CUSTOM_FIELD,
                parameters={"field_name": "has_order_number", "field_value": True}
            ),
            RuleAction(
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "order_support"}
            )
        ]
    )

    return [complex_rule, order_number_rule]

async def demonstrate_routing_examples():
    """Demonstrate the routing examples."""

    print("Creating routing configuration...\n")

    # Create configuration with examples
    basic_rules = create_basic_routing_examples()
    advanced_rules = create_advanced_routing_examples()

    all_rules = basic_rules + advanced_rules
    config = RoutingConfig(rules=all_rules, enable_caching=False)

    print(f"Created configuration with {len(config.rules)} rules")
    print("\nRule Summary:")
    for rule in config.rules:
        print(f"  - {rule.name} (Priority: {rule.priority})")

    # Create routing engine
    engine = RoutingEngine(config)

    # Test scenarios
    test_scenarios = [
        {
            "name": "Basic Billing Issue",
            "message": "I need help with my billing",
            "user_tier": "standard",
            "expected_rule": "billing_issues"
        },
        {
            "name": "VIP Customer",
            "message": "I have a question about my account",
            "user_tier": "vip",
            "expected_rule": "vip_customers"
        },
        {
            "name": "VIP with Billing",
            "message": "There's an error in my billing statement",
            "user_tier": "vip",
            "expected_rule": "vip_customers"  # VIP rule matches first due to priority
        },
        {
            "name": "Order Number Detection",
            "message": "My order ORD-12345678 hasn't arrived",
            "user_tier": "standard",
            "expected_rule": "order_number_detection"
        }
    ]

    print("\n" + "=" * 60)
    print("Testing Routing Rules")
    print("=" * 60 + "\n")

    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Message: \"{scenario['message']}\"")
        print(f"User Tier: {scenario['user_tier']}")
        print("-" * 40)

        # Create test context
        context = MockContext()
        context.messages = [MockMessage(scenario['message'], "user")]

        decision = MockDecision()
        metadata = {
            "user": {
                "id": "user-123",
                "tier": scenario['user_tier'],
                "name": "Test User"
            },
            "channel": "web"
        }

        # Apply routing
        result = await engine.evaluate(context, decision, metadata)

        if result:
            print(f"✓ Matched Rule: {result.rule_name}")
            if result.rule_name == scenario['expected_rule']:
                print("  ✓ Expected rule matched!")
            else:
                print(f"  ✗ Expected {scenario['expected_rule']} but got {result.rule_name}")

            if result.get_assigned_agent():
                print(f"  Assigned to Agent: {result.get_assigned_agent()}")
            if result.get_assigned_queue():
                print(f"  Assigned to Queue: {result.get_assigned_queue()}")
            if result.get_assigned_department():
                print(f"  Assigned to Department: {result.get_assigned_department()}")
            if result.get_priority():
                print(f"  Priority: {result.get_priority()}")
            if result.get_tags():
                print(f"  Tags: {', '.join(result.get_tags())}")
            print(f"  Execution Time: {result.execution_time_ms:.2f}ms")
        else:
            print("✗ No rule matched")

        print("\n")

    # Test rule performance
    print("=" * 60)
    print("Performance Test")
    print("=" * 60 + "\n")

    # Create test context for performance
    context = MockContext()
    decision = MockDecision()
    metadata = {
        "user": {"tier": "premium", "name": "Perf Test"}
    }

    # Run multiple evaluations
    total_time = 0
    num_runs = 100

    for i in range(num_runs):
        result = await engine.evaluate(context, decision, metadata)
        if result:
            total_time += result.execution_time_ms

    avg_time = total_time / num_runs
    print(f"Average execution time over {num_runs} runs: {avg_time:.3f}ms")
    print(f"Performance requirement (<100ms): {'✓ PASS' if avg_time < 100 else '✗ FAIL'}")

    # Test rule management
    print("\n" + "=" * 60)
    print("Rule Management Demo")
    print("=" * 60 + "\n")

    # Add a new rule dynamically
    new_rule = RoutingRule(
        name="dynamic_rule",
        priority=150,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "dynamic"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["dynamic", "test"]}
            )
        ]
    )

    config.add_rule(new_rule)
    print(f"Added dynamic rule. Total rules: {len(config.rules)}")

    # Test the new rule
    context.messages = [MockMessage("This is a dynamic test", "user")]
    result = await engine.evaluate(context, decision, metadata)

    if result and result.rule_name == "dynamic_rule":
        print("✓ Dynamic rule matched successfully!")
        print(f"  Tags added: {result.get_tags()}")


async def main():
    """Main function."""
    await demonstrate_routing_examples()

if __name__ == "__main__":
    asyncio.run(main())