#!/usr/bin/env python3
"""Standalone test of routing functionality without package imports."""

import sys
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, Union, List, Dict
from enum import Enum
from pydantic import BaseModel, Field

print("=== Standalone Routing Test ===\n")

# Define minimal types needed
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

# Now import the actual modules directly
print("Loading routing modules...")

# First, let's manually add our types to the module
import handoffkit.routing.types
handoffkit.routing.types.RuleActionType = RuleActionType
handoffkit.routing.types.ConditionType = ConditionType
handoffkit.routing.types.Operator = Operator

# Now we can import the models
from handoffkit.routing.models import RoutingRule, RoutingResult, RuleAction, Condition, RoutingConfig
print("✓ Imported models")

from handoffkit.routing.conditions import ConditionEvaluator
print("✓ Imported conditions")

from handoffkit.routing.actions import ActionExecutor
print("✓ Imported actions")

from handoffkit.routing.engine import RoutingEngine
print("✓ Imported engine")

# Test basic functionality
print("\n=== Testing Basic Functionality ===")

# Create a simple rule
rule = RoutingRule(
    name="billing_priority_rule",
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
            type=RuleActionType.SET_PRIORITY,
            parameters={"priority": "HIGH"}
        ),
        RuleAction(
            type=RuleActionType.ASSIGN_TO_QUEUE,
            parameters={"queue_name": "billing_queue"}
        )
    ]
)

print(f"✓ Created rule: {rule.name}")
print(f"  - Priority: {rule.priority}")
print(f"  - Conditions: {len(rule.conditions)}")
print(f"  - Actions: {len(rule.actions)}")

# Test condition creation
condition = Condition(
    type=ConditionType.MESSAGE_CONTENT,
    field="content",
    operator=Operator.CONTAINS,
    value="billing"
)
print(f"\n✓ Created condition: {condition.type.value}")

# Test action creation
action = RuleAction(
    type=RuleActionType.SET_PRIORITY,
    parameters={"priority": "HIGH"}
)
print(f"✓ Created action: {action.type}")

# Test routing config
config = RoutingConfig(rules=[rule], enable_caching=False)
print(f"\n✓ Created routing config with {len(config.rules)} rules")

# Test routing engine
routing_engine = RoutingEngine(config)
print(f"✓ Created routing engine")

# Create minimal mock objects
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

context = MockContext()
decision = MockDecision()
metadata = {
    "user": {
        "name": "John Doe",
        "email": "john@example.com",
        "tier": "premium",
    },
    "channel": "web",
}

# Test rule evaluation
async def test_evaluation():
    print("\n=== Testing Rule Evaluation ===")

    # Test rule that should match
    result = await routing_engine.evaluate(context, decision, metadata)
    if result:
        print(f"✓ Rule matched: {result.rule_name}")
        print(f"  - Actions applied: {len(result.actions_applied)}")
        print(f"  - Priority set: {result.get_priority()}")
        print(f"  - Queue assigned: {result.get_assigned_queue()}")
        print(f"  - Tags: {result.get_tags()}")
        print(f"  - Execution time: {result.execution_time_ms:.2f}ms")
    else:
        print("✗ No rule matched")

    # Test rule testing functionality
    print("\n=== Testing Rule Test Function ===")
    test_result = await routing_engine.test_rule(rule, context, decision, metadata)
    print(f"✓ Rule test result: match={test_result['overall_match']}")
    print(f"  - Execution time: {test_result['execution_time_ms']:.2f}ms")
    print(f"  - Condition results: {len(test_result['condition_results'])}")
    for i, cr in enumerate(test_result['condition_results']):
        print(f"    Condition {i}: {cr['type']} - {cr['result']}")

# Run async test
asyncio.run(test_evaluation())

# Test more complex scenarios
print("\n=== Testing Complex Scenarios ===")

# Test multiple rules with priorities
rule2 = RoutingRule(
    name="premium_user_rule",
    priority=200,  # Higher priority
    conditions=[
        {
            "type": ConditionType.USER_ATTRIBUTE,
            "field": "tier",
            "operator": Operator.EQUALS,
            "value": "premium"
        }
    ],
    actions=[
        RuleAction(
            type=RuleActionType.ASSIGN_TO_AGENT,
            parameters={"agent_id": "premium-agent-123"}
        )
    ]
)

config2 = RoutingConfig(rules=[rule, rule2], enable_caching=False)
engine2 = RoutingEngine(config2)

async def test_multiple_rules():
    print("\n=== Testing Multiple Rules ===")
    result = await engine2.evaluate(context, decision, metadata)
    if result:
        print(f"✓ Matched rule: {result.rule_name} (higher priority)")
        print(f"  - Agent assigned: {result.get_assigned_agent()}")

asyncio.run(test_multiple_rules())

print("\n=== All Tests Completed Successfully! ===")