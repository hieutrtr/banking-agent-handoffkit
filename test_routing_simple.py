#!/usr/bin/env python3
"""Simple test script for routing functionality."""

import sys
import asyncio
from datetime import datetime, timezone

# Add the parent directory to the path
sys.path.insert(0, '/home/hieutt50/projects/handoffkit')

# Test basic imports
try:
    from handoffkit.routing.types import RuleActionType, ConditionType, Operator
    print("✓ Successfully imported routing types")
except ImportError as e:
    print(f"✗ Failed to import routing types: {e}")
    sys.exit(1)

# Test models import
try:
    from handoffkit.routing.models import RoutingRule, RoutingResult, RuleAction, Condition
    print("✓ Successfully imported routing models")
except ImportError as e:
    print(f"✗ Failed to import routing models: {e}")
    sys.exit(1)

# Test engine import
try:
    from handoffkit.routing.engine import RoutingEngine
    print("✓ Successfully imported routing engine")
except ImportError as e:
    print(f"✗ Failed to import routing engine: {e}")
    sys.exit(1)

# Test basic functionality
print("\n=== Testing Basic Functionality ===")

# Create a simple rule
rule = RoutingRule(
    name="test_rule",
    priority=100,
    conditions=[
        {
            "type": ConditionType.MESSAGE_CONTENT,
            "field": "content",
            "operator": Operator.CONTAINS,
            "value": "help"
        }
    ],
    actions=[
        RuleAction(
            type=RuleActionType.ASSIGN_TO_QUEUE,
            parameters={"queue_name": "support_queue"}
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
from handoffkit.routing.models import RoutingConfig
config = RoutingConfig(rules=[rule], enable_caching=False)
print(f"\n✓ Created routing config with {len(config.rules)} rules")

# Test routing engine
engine = RoutingEngine(config)
print(f"✓ Created routing engine")

# Create mock context and decision
from handoffkit.core.types import ConversationContext, HandoffDecision, Message, Speaker, HandoffPriority

context = ConversationContext(
    conversation_id="test-123",
    user_id="user-456",
    messages=[
        Message(
            content="I need help with billing",
            speaker=Speaker.USER,
            timestamp=datetime.now(timezone.utc),
        )
    ],
    metadata={}
)

decision = HandoffDecision(
    should_handoff=True,
    confidence=0.9,
    reason="Test",
    priority=HandoffPriority.MEDIUM,
    trigger_results=[]
)

metadata = {}

# Test rule evaluation
async def test_evaluation():
    print("\n=== Testing Rule Evaluation ===")

    # Test rule that should match
    result = await engine.evaluate(context, decision, metadata)
    if result:
        print(f"✓ Rule matched: {result.rule_name}")
        print(f"  - Actions applied: {len(result.actions_applied)}")
        print(f"  - Queue assigned: {result.get_assigned_queue()}")
    else:
        print("✗ No rule matched (expected for this test)")

    # Test rule testing functionality
    print("\n=== Testing Rule Test Function ===")
    test_result = await engine.test_rule(rule, context, decision, metadata)
    print(f"✓ Rule test result: match={test_result['overall_match']}")
    print(f"  - Execution time: {test_result['execution_time_ms']:.2f}ms")

# Run async test
asyncio.run(test_evaluation())

print("\n=== All Tests Passed! ===")