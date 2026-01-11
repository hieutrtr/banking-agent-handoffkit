# Routing Rules Guide

This guide provides comprehensive examples and best practices for creating routing rules in HandoffKit.

## Table of Contents

1. [Basic Routing Examples](#basic-routing-examples)
2. [Advanced Routing Patterns](#advanced-routing-patterns)
3. [Condition Types](#condition-types)
4. [Action Types](#action-types)
5. [Best Practices](#best-practices)
6. [Performance Considerations](#performance-considerations)
7. [Common Use Cases](#common-use-cases)

## Basic Routing Examples

### 1. Simple Keyword-Based Routing

Route messages containing specific keywords to appropriate queues:

```python
from handoffkit.routing import RoutingRule, RuleAction, ConditionType, Operator, RuleActionType

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
        )
    ]
)
```

### 2. User Tier-Based Routing

Route VIP customers to specialized agents:

```python
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
            parameters={"agent_id": "senior-agent-001"}
        ),
        RuleAction(
            type=RuleActionType.SET_PRIORITY,
            parameters={"priority": "URGENT"}
        )
    ]
)
```

### 3. Department-Based Routing

Route to specific departments based on issue type:

```python
technical_rule = RoutingRule(
    name="technical_issues",
    priority=90,
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
        )
    ]
)
```

## Advanced Routing Patterns

### 1. Multi-Condition Rules

Rules with multiple conditions (AND logic):

```python
urgent_vip_billing = RoutingRule(
    name="urgent_vip_billing",
    priority=300,
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
        },
        {
            "type": ConditionType.MESSAGE_CONTENT,
            "field": "content",
            "operator": Operator.CONTAINS,
            "value": "urgent"
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
```

### 2. Regex Pattern Matching

Use regular expressions for complex pattern detection:

```python
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
```

### 3. Negation Rules

Use negation to handle exceptions:

```python
non_english_rule = RoutingRule(
    name="non_english_routing",
    priority=70,
    conditions=[
        {
            "type": ConditionType.MESSAGE_CONTENT,
            "field": "content",
            "operator": Operator.REGEX_MATCHES,
            "value": r"^[a-zA-Z\s.,!?]+$",
            "negate": True  # NOT matching English pattern
        }
    ],
    actions=[
        RuleAction(
            type=RuleActionType.ASSIGN_TO_QUEUE,
            parameters={"queue_name": "multilingual_support"}
        )
    ]
)
```

### 4. Time-Based Routing

Route based on time of day:

```python
after_hours_rule = RoutingRule(
    name="after_hours_support",
    priority=80,
    conditions=[
        {
            "type": ConditionType.TIME_BASED,
            "operator": Operator.AFTER,
            "value": "18:00"  # After 6 PM
        }
    ],
    actions=[
        RuleAction(
            type=RuleActionType.ASSIGN_TO_QUEUE,
            parameters={"queue_name": "after_hours_support"}
        )
    ]
)
```

## Condition Types

### Message Content Conditions

```python
# Check message content
{
    "type": ConditionType.MESSAGE_CONTENT,
    "field": "content",  # or "speaker", "timestamp", "length"
    "operator": Operator.CONTAINS,
    "value": "billing"
}

# Check message length
{
    "type": ConditionType.MESSAGE_CONTENT,
    "field": "length",
    "operator": Operator.GREATER_THAN,
    "value": 10
}
```

### User Attribute Conditions

```python
# Check user tier
{
    "type": ConditionType.USER_ATTRIBUTE,
    "field": "tier",
    "operator": Operator.EQUALS,
    "value": "premium"
}

# Check if user has specific attribute
{
    "type": ConditionType.USER_ATTRIBUTE,
    "field": "subscription_status",
    "operator": Operator.EQUALS,
    "value": "active"
}
```

### Context Field Conditions

```python
# Check communication channel
{
    "type": ConditionType.CONTEXT_FIELD,
    "field": "channel",
    "operator": Operator.EQUALS,
    "value": "web"
}

# Check conversation metadata
{
    "type": ConditionType.CONTEXT_FIELD,
    "field": "region",
    "operator": Operator.EQUALS,
    "value": "US"
}
```

### Entity Conditions

```python
# Check for specific entity
{
    "type": ConditionType.ENTITY,
    "field": "product_name",
    "operator": Operator.EQUALS,
    "value": "PremiumWidget"
}
```

### Metadata Conditions

```python
# Check sentiment score
{
    "type": ConditionType.METADATA,
    "field": "sentiment_score",
    "operator": Operator.LESS_THAN,
    "value": 0.3
}
```

### Trigger Conditions

```python
# Check trigger type
{
    "type": ConditionType.TRIGGER,
    "field": "trigger_type",
    "operator": Operator.EQUALS,
    "value": "keyword_match"
}

# Check trigger confidence
{
    "type": ConditionType.TRIGGER,
    "field": "confidence",
    "operator": Operator.GREATER_THAN,
    "value": 0.8
}
```

## Action Types

### Assignment Actions

```python
# Assign to specific agent
RuleAction(
    type=RuleActionType.ASSIGN_TO_AGENT,
    parameters={"agent_id": "agent-123"}
)

# Assign to queue
RuleAction(
    type=RuleActionType.ASSIGN_TO_QUEUE,
    parameters={"queue_name": "billing_support"}
)

# Assign to department
RuleAction(
    type=RuleActionType.ASSIGN_TO_DEPARTMENT,
    parameters={"department": "technical_support"}
)
```

### Priority Actions

```python
# Set priority
RuleAction(
    type=RuleActionType.SET_PRIORITY,
    parameters={"priority": "HIGH"}  # LOW, MEDIUM, HIGH, URGENT, CRITICAL
)
```

### Tag Actions

```python
# Add tags
RuleAction(
    type=RuleActionType.ADD_TAGS,
    parameters={"tags": ["billing", "urgent", "vip"]}
)

# Remove tags
RuleAction(
    type=RuleActionType.REMOVE_TAGS,
    parameters={"tags": ["low_priority"]}
)
```

### Custom Field Actions

```python
# Set custom field
RuleAction(
    type=RuleActionType.SET_CUSTOM_FIELD,
    parameters={"field_name": "customer_type", "field_value": "enterprise"}
)
```

### Fallback Actions

```python
# Route to fallback
RuleAction(
    type=RuleActionType.ROUTE_TO_FALLBACK,
    parameters={"reason": "no_agents_available"}
)
```

## Best Practices

### 1. Rule Priority Management

- Use priority ranges (1-1000) consistently
- Reserve high priorities (800-1000) for critical rules
- Use medium priorities (400-799) for standard rules
- Use low priorities (1-399) for fallback/catch-all rules

### 2. Condition Ordering

- Place faster conditions first (e.g., simple string checks before regex)
- Place more specific conditions before general ones
- Use short-circuit evaluation to your advantage

### 3. Action Efficiency

- Combine multiple actions in a single rule when possible
- Use tags for categorization that doesn't require assignment
- Set custom fields for data that needs to persist

### 4. Rule Organization

```python
# Use descriptive names
billing_urgent_vip_rule = RoutingRule(
    name="billing_urgent_vip_escalation",  # Clear and descriptive
    # ...
)

# Add metadata for documentation
rule = RoutingRule(
    name="billing_urgent_vip",
    # ...
    metadata={
        "description": "Escalate urgent billing issues from VIP customers",
        "tags": ["vip", "billing", "urgent"],
        "created_by": "admin@company.com",
        "business_reason": "VIP customers need immediate attention"
    }
)
```

## Performance Considerations

### 1. Rule Evaluation Order

Rules are evaluated by priority (highest first). Place frequently matching rules at higher priorities to avoid unnecessary evaluations.

### 2. Caching

Enable caching for better performance:

```python
config = RoutingConfig(
    rules=rules,
    enable_caching=True,
    cache_ttl_seconds=300  # 5 minutes
)
```

### 3. Condition Optimization

- Use simple operators (EQUALS, CONTAINS) when possible
- Avoid expensive regex operations in high-traffic rules
- Limit the number of conditions per rule (max 20)

## Common Use Cases

### 1. Customer Tier-Based Routing

```python
def create_tier_based_routing():
    return [
        RoutingRule(
            name="enterprise_customers",
            priority=250,
            conditions=[
                {
                    "type": ConditionType.USER_ATTRIBUTE,
                    "field": "tier",
                    "operator": Operator.EQUALS,
                    "value": "enterprise"
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_AGENT, parameters={"agent_id": "enterprise-specialist"}),
                RuleAction(type=RuleActionType.SET_PRIORITY, parameters={"priority": "CRITICAL"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["enterprise", "high_value"]})
            ]
        ),
        RoutingRule(
            name="premium_customers",
            priority=200,
            conditions=[
                {
                    "type": ConditionType.USER_ATTRIBUTE,
                    "field": "tier",
                    "operator": Operator.EQUALS,
                    "value": "premium"
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_QUEUE, parameters={"queue_name": "premium_support"}),
                RuleAction(type=RuleActionType.SET_PRIORITY, parameters={"priority": "HIGH"})
            ]
        ),
        RoutingRule(
            name="standard_customers",
            priority=100,
            conditions=[
                {
                    "type": ConditionType.USER_ATTRIBUTE,
                    "field": "tier",
                    "operator": Operator.EQUALS,
                    "value": "standard"
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_QUEUE, parameters={"queue_name": "standard_support"})
            ]
        )
    ]
```

### 2. Issue Type Routing

```python
def create_issue_type_routing():
    return [
        RoutingRule(
            name="billing_issues",
            priority=120,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.IN_LIST,
                    "value": ["billing", "invoice", "payment", "charge"]
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_QUEUE, parameters={"queue_name": "billing"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["billing", "financial"]})
            ]
        ),
        RoutingRule(
            name="technical_issues",
            priority=110,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.IN_LIST,
                    "value": ["error", "bug", "crash", "not working"]
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_DEPARTMENT, parameters={"department": "technical"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["technical", "bug"]})
            ]
        ),
        RoutingRule(
            name="account_issues",
            priority=115,
            conditions=[
                {
                    "type": ConditionType.MESSAGE_CONTENT,
                    "field": "content",
                    "operator": Operator.IN_LIST,
                    "value": ["account", "login", "password", "access"]
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_QUEUE, parameters={"queue_name": "account_support"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["account", "access"]}
            )
        ]
    ]
```

### 3. Escalation Rules

```python
def create_escalation_rules():
    return [
        RoutingRule(
            name="negative_sentiment_escalation",
            priority=250,
            conditions=[
                {
                    "type": ConditionType.METADATA,
                    "field": "sentiment_score",
                    "operator": Operator.LESS_THAN,
                    "value": 0.2
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_DEPARTMENT, parameters={"department": "escalation"}),
                RuleAction(type=RuleActionType.SET_PRIORITY, parameters={"priority": "URGENT"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["escalation", "negative_sentiment"]})
            ]
        ),
        RoutingRule(
            name="multiple_failures_escalation",
            priority=240,
            conditions=[
                {
                    "type": ConditionType.METADATA,
                    "field": "failure_count",
                    "operator": Operator.GREATER_THAN,
                    "value": 3
                }
            ],
            actions=[
                RuleAction(type=RuleActionType.ASSIGN_TO_AGENT, parameters={"agent_id": "senior-agent"}),
                RuleAction(type=RuleActionType.SET_PRIORITY, parameters={"priority": "HIGH"}),
                RuleAction(type=RuleActionType.ADD_TAGS, parameters={"tags": ["escalation", "multiple_failures"]})
            ]
        )
    ]
```

## Testing Your Rules

### 1. Test Individual Rules

```python
from handoffkit.routing import RoutingEngine

# Create test context and decision
context = ConversationContext(
    conversation_id="test-123",
    user_id="user-456",
    messages=[
        Message(
            content="I need help with billing",
            speaker=Speaker.USER,
            timestamp=datetime.now(timezone.utc)
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

metadata = {
    "user": {"tier": "premium", "name": "John Doe"}
}

# Test the rule
engine = RoutingEngine(config)
result = await engine.test_rule(rule, context, decision, metadata)
print(f"Rule matched: {result['overall_match']}")
print(f"Condition results: {result['condition_results']}")
```

### 2. Profile Rule Performance

```python
from handoffkit.routing.engine import RulePerformanceProfiler

profiler = RulePerformanceProfiler(engine)
results = await profiler.profile_rules(context, decision, metadata)

print(f"Total evaluation time: {results['total_evaluation_time_ms']}ms")
for rule_result in results['rule_evaluations']:
    print(f"{rule_result['rule_name']}: {rule_result['execution_time_ms']}ms")
```

---

## Summary

The routing rules system in HandoffKit provides powerful capabilities for intelligent conversation routing. By combining different condition types, operators, and actions, you can create sophisticated routing logic tailored to your specific business needs.

Key features to remember:
- Priority-based evaluation (higher priority rules evaluated first)
- Multiple condition types for flexible matching
- Rich set of actions for routing and metadata management
- Performance optimizations with caching
- Async/await support for non-blocking operations

For more examples, see the `routing_rules_examples.py` file in the examples directory.