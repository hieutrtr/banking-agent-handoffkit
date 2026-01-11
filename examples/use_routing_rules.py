#!/usr/bin/env python3
"""
Practical example of using HandoffKit routing rules.

This script demonstrates how to:
1. Create routing rules
2. Configure the routing engine
3. Test rules with sample conversations
4. Handle rule-based routing in your application
"""

import asyncio
import json
from datetime import datetime, timezone

from handoffkit.core.types import ConversationContext, HandoffDecision, Message, Speaker, HandoffPriority, TriggerResult
from handoffkit.routing import (
    RoutingEngine,
    RoutingRule,
    RoutingConfig,
    RuleAction,
    RuleActionType,
    ConditionType,
    Operator,
)


async def create_sample_routing_config() -> RoutingConfig:
    """Create a sample routing configuration with practical rules."""

    # Rule 1: VIP customers get priority routing
    vip_rule = RoutingRule(
        name="vip_customer_priority",
        priority=200,  # High priority
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
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["vip", "priority"]}
            )
        ]
    )

    # Rule 2: Billing issues go to billing queue
    billing_rule = RoutingRule(
        name="billing_issues",
        priority=150,
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
            )
        ]
    )

    # Rule 3: Technical errors to technical support
    technical_rule = RoutingRule(
        name="technical_errors",
        priority=140,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "error"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_DEPARTMENT,
                parameters={"department": "technical_support"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["technical", "error"]}
            )
        ]
    )

    # Rule 4: Negative sentiment escalation
    sentiment_rule = RoutingRule(
        name="negative_sentiment_escalation",
        priority=180,
        conditions=[
            {
                "type": ConditionType.METADATA,
                "field": "sentiment_score",
                "operator": Operator.LESS_THAN,
                "value": 0.3
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_DEPARTMENT,
                parameters={"department": "escalation_team"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "HIGH"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["escalation", "negative_sentiment"]}
            )
        ]
    )

    # Rule 5: After-hours routing
    after_hours_rule = RoutingRule(
        name="after_hours_support",
        priority=100,
        conditions=[
            {
                "type": ConditionType.TIME_BASED,
                "operator": Operator.AFTER,
                "value": "18:00"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "after_hours"}
            ),
            RuleAction(
                type=RuleActionType.SET_CUSTOM_FIELD,
                parameters={"field_name": "business_hours", "field_value": "after_hours"}
            )
        ]
    )

    # Create configuration
    config = RoutingConfig(
        rules=[
            vip_rule,
            sentiment_rule,
            billing_rule,
            technical_rule,
            after_hours_rule
        ],
        enable_caching=True,
        cache_ttl_seconds=300,
        max_evaluation_time_ms=100
    )

    return config


async def simulate_conversation(
    engine: RoutingEngine,
    user_message: str,
    user_attributes: dict,
    metadata: dict
) -> dict:
    """Simulate a conversation and apply routing rules."""

    # Create conversation context
    context = ConversationContext(
        conversation_id=f"conv-{int(datetime.now().timestamp())}",
        user_id=user_attributes.get("id", "user-123"),
        messages=[
            Message(
                content=user_message,
                speaker=Speaker.USER,
                timestamp=datetime.now(timezone.utc)
            )
        ],
        metadata={
            "extracted_entities": [
                {"entity_type": "issue_type", "value": "support"}
            ],
            "sentiment_score": metadata.get("sentiment_score", 0.5)
        }
    )

    # Create handoff decision
    decision = HandoffDecision(
        should_handoff=True,
        confidence=0.85,
        reason="Customer needs human assistance",
        priority=HandoffPriority.MEDIUM,
        trigger_results=[
            TriggerResult(
                trigger_type="keyword_match",
                confidence=0.85,
                reason="Support keyword detected",
                metadata={"keyword": "help"}
            )
        ]
    )

    # Apply routing rules
    result = await engine.evaluate(context, decision, metadata)

    if result:
        return {
            "matched_rule": result.rule_name,
            "assigned_agent": result.get_assigned_agent(),
            "assigned_queue": result.get_assigned_queue(),
            "assigned_department": result.get_assigned_department(),
            "priority": result.get_priority(),
            "tags": result.get_tags(),
            "execution_time_ms": result.execution_time_ms,
            "custom_fields": result.metadata.get("routing_custom_fields", {})
        }
    else:
        return {
            "matched_rule": None,
            "message": "No routing rules matched - using default routing"
        }


async def run_routing_examples():
    """Run examples of routing in action."""

    print("HandoffKit Routing Rules Demo")
    print("=" * 50 + "\n")

    # Create routing configuration
    config = await create_sample_routing_config()
    print(f"Created routing configuration with {len(config.rules)} rules\n")

    # Create routing engine
    engine = RoutingEngine(config)

    # Example scenarios
    scenarios = [
        {
            "name": "VIP Customer with Billing Issue",
            "message": "I need help with my billing, there's an error in my invoice",
            "user_attributes": {"id": "user-001", "tier": "vip", "name": "John Doe"},
            "metadata": {"sentiment_score": 0.7}
        },
        {
            "name": "Regular Customer Technical Issue",
            "message": "I'm getting an error when trying to access my account",
            "user_attributes": {"id": "user-002", "tier": "standard", "name": "Jane Smith"},
            "metadata": {"sentiment_score": 0.5}
        },
        {
            "name": "Customer with Negative Sentiment",
            "message": "This is terrible! Nothing works and I'm very frustrated!",
            "user_attributes": {"id": "user-003", "tier": "standard", "name": "Bob Johnson"},
            "metadata": {"sentiment_score": 0.1}
        },
        {
            "name": "After Hours Inquiry",
            "message": "I have a question about my billing",
            "user_attributes": {"id": "user-004", "tier": "premium", "name": "Alice Brown"},
            "metadata": {"sentiment_score": 0.8}
        }
    ]

    # Run each scenario
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Message: \"{scenario['message']}\"")
        print(f"User: {scenario['user_attributes']['name']} (Tier: {scenario['user_attributes']['tier']})")
        print(f"Sentiment: {scenario['metadata']['sentiment_score']}")
        print("-" * 40)

        # Apply routing
        result = await simulate_conversation(
            engine,
            scenario['message'],
            scenario['user_attributes'],
            scenario['metadata']
        )

        # Display results
        if result['matched_rule']:
            print(f"✓ Matched Rule: {result['matched_rule']}")

            if result['assigned_agent']:
                print(f"  Assigned to Agent: {result['assigned_agent']}")
            if result['assigned_queue']:
                print(f"  Assigned to Queue: {result['assigned_queue']}")
            if result['assigned_department']:
                print(f"  Assigned to Department: {result['assigned_department']}")
            if result['priority']:
                print(f"  Priority: {result['priority']}")
            if result['tags']:
                print(f"  Tags: {', '.join(result['tags'])}")
            if result['custom_fields']:
                print(f"  Custom Fields: {result['custom_fields']}")

            print(f"  Execution Time: {result['execution_time_ms']:.2f}ms")
        else:
            print(f"✗ {result['message']}")

        print("\n")

    # Test rule performance profiling
    print("Rule Performance Profiling")
    print("-" * 30)

    from handoffkit.routing.engine import RulePerformanceProfiler
    profiler = RulePerformanceProfiler(engine)

    # Create test context
    context = ConversationContext(
        conversation_id="perf-test-123",
        user_id="user-perf",
        messages=[
            Message(
                content="Test message for performance profiling",
                speaker=Speaker.USER,
                timestamp=datetime.now(timezone.utc)
            )
        ],
        metadata={}
    )

    decision = HandoffDecision(
        should_handoff=True,
        confidence=0.9,
        reason="Performance test",
        priority=HandoffPriority.MEDIUM,
        trigger_results=[]
    )

    # Profile performance
    perf_results = await profiler.profile_rules(context, decision, {})

    print(f"Total evaluation time: {perf_results['total_evaluation_time_ms']:.2f}ms")
    print(f"Rules evaluated: {len(perf_results['rule_evaluations'])}")

    # Show slowest rules
    slow_rules = sorted(
        perf_results['rule_evaluations'],
        key=lambda x: x['execution_time_ms'],
        reverse=True
    )[:3]

    print("\nTop 3 slowest rules:")
    for rule in slow_rules:
        print(f"  {rule['rule_name']}: {rule['execution_time_ms']:.2f}ms")

    print("\n" + "=" * 50)
    print("Demo completed successfully!")

    print("\nKey takeaways:")
    print("- Rules are evaluated by priority (higher first)")
    print("- Multiple conditions use AND logic")
    print("- Actions are executed in order")
    print("- Performance is optimized (<100ms per evaluation)")
    print("- Rules can be dynamically added/updated")


async def test_rule_configuration():
    """Test configuring and managing routing rules."""

    print("\n\nRule Configuration Management")
    print("=" * 50 + "\n")

    # Create initial configuration
    config = RoutingConfig()

    # Add rules one by one
    rule1 = RoutingRule(
        name="rule_1",
        priority=100,
        conditions=[],
        actions=[]
    )
    config.add_rule(rule1)
    print(f"Added rule 'rule_1'. Total rules: {len(config.rules)}")

    # Add another rule
    rule2 = RoutingRule(
        name="rule_2",
        priority=50,
        conditions=[],
        actions=[]
    )
    config.add_rule(rule2)
    print(f"Added rule 'rule_2'. Total rules: {len(config.rules)}")

    # Check priority ordering
    print("\nRule order (by priority):")
    for i, rule in enumerate(config.rules):
        print(f"  {i+1}. {rule.name} (Priority: {rule.priority})")

    # Remove a rule
    removed = config.remove_rule("rule_1")
    print(f"\nRemoved 'rule_1': {removed}")
    print(f"Total rules now: {len(config.rules)}")

    # Try to add duplicate
    try:
        config.add_rule(rule2)  # Same name
    except ValueError as e:
        print(f"\nDuplicate rule error: {e}")

    # Export configuration
    config_dict = config.model_dump()
    print(f"\nConfiguration export (first rule only):")
    print(json.dumps(config_dict["rules"][0], indent=2)[:500] + "...")


async def main():
    """Main function to run all examples."""
    await run_routing_examples()
    await test_rule_configuration()


if __name__ == "__main__":
    asyncio.run(main())