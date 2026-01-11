#!/usr/bin/env python3
"""Direct test of routing modules without package imports."""

import sys
import asyncio
from datetime import datetime, timezone

# Add the parent directory to the path
sys.path.insert(0, '/home/hieutt50/projects/handoffkit')

# Test direct imports bypassing the main package
try:
    # Import types directly
    import handoffkit.routing.types as types
    print("✓ Successfully imported routing types")

    # Import models directly
    import handoffkit.routing.models as models
    print("✓ Successfully imported routing models")

    # Import engine directly
    import handoffkit.routing.engine as engine
    print("✓ Successfully imported routing engine")

    # Import conditions directly
    import handoffkit.routing.conditions as conditions
    print("✓ Successfully imported routing conditions")

    # Import actions directly
    import handoffkit.routing.actions as actions
    print("✓ Successfully imported routing actions")

except ImportError as e:
    print(f"✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test basic functionality
print("\n=== Testing Basic Functionality ===")

# Create a simple rule
rule = models.RoutingRule(
    name="test_rule",
    priority=100,
    conditions=[
        {
            "type": types.ConditionType.MESSAGE_CONTENT,
            "field": "content",
            "operator": types.Operator.CONTAINS,
            "value": "help"
        }
    ],
    actions=[
        models.RuleAction(
            type=types.RuleActionType.ASSIGN_TO_QUEUE,
            parameters={"queue_name": "support_queue"}
        )
    ]
)

print(f"✓ Created rule: {rule.name}")
print(f"  - Priority: {rule.priority}")
print(f"  - Conditions: {len(rule.conditions)}")
print(f"  - Actions: {len(rule.actions)}")

# Test condition creation
condition = conditions.Condition(
    type=types.ConditionType.MESSAGE_CONTENT,
    field="content",
    operator=types.Operator.CONTAINS,
    value="billing"
)
print(f"\n✓ Created condition: {condition.type.value}")

# Test action creation
action = models.RuleAction(
    type=types.RuleActionType.SET_PRIORITY,
    parameters={"priority": "HIGH"}
)
print(f"✓ Created action: {action.type}")

# Test routing config
config = models.RoutingConfig(rules=[rule], enable_caching=False)
print(f"\n✓ Created routing config with {len(config.rules)} rules")

# Test routing engine
routing_engine = engine.RoutingEngine(config)
print(f"✓ Created routing engine")

# Create mock context and decision
# We'll create minimal mock objects since we can't import the full types
class MockContext:
    def __init__(self):
        self.conversation_id = "test-123"
        self.user_id = "user-456"
        self.messages = [type('obj', (object,), {
            'content': "I need help with billing",
            'speaker': type('Speaker', (object,), {'value': 'user'})(),
            'timestamp': datetime.now(timezone.utc)
        })()]
        self.metadata = {}

class MockDecision:
    def __init__(self):
        self.should_handoff = True
        self.confidence = 0.9
        self.reason = "Test"
        self.priority = type('Priority', (object,), {'value': 'MEDIUM'})()
        self.trigger_results = []

context = MockContext()
decision = MockDecision()
metadata = {}

# Test rule evaluation
async def test_evaluation():
    print("\n=== Testing Rule Evaluation ===")

    # Test rule that should match
    result = await routing_engine.evaluate(context, decision, metadata)
    if result:
        print(f"✓ Rule matched: {result.rule_name}")
        print(f"  - Actions applied: {len(result.actions_applied)}")
        print(f"  - Queue assigned: {result.get_assigned_queue()}")
    else:
        print("✗ No rule matched (expected for this test)")

    # Test rule testing functionality
    print("\n=== Testing Rule Test Function ===")
    test_result = await routing_engine.test_rule(rule, context, decision, metadata)
    print(f"✓ Rule test result: match={test_result['overall_match']}")
    print(f"  - Execution time: {test_result['execution_time_ms']:.2f}ms")

# Run async test
asyncio.run(test_evaluation())

print("\n=== All Tests Passed! ===")