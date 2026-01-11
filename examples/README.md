# HandoffKit Routing Rules Examples

This directory contains comprehensive examples of using HandoffKit's routing rules system.

## Files

1. **routing_rules_examples.py** - Comprehensive examples of all routing rule features
2. **use_routing_rules.py** - Practical demonstration of using routing rules in your application
3. **test_routing_standalone.py** - Standalone test of routing functionality

## Quick Start

### 1. Basic Rule Creation

```python
from handoffkit.routing import RoutingRule, RuleAction, ConditionType, Operator, RuleActionType

# Create a simple billing rule
rule = RoutingRule(
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
        )
    ]
)
```

### 2. Run the Examples

```bash
# Run the comprehensive examples
python routing_rules_examples.py

# Run the practical usage demo
python use_routing_rules.py

# Run standalone test
python test_routing_standalone.py
```

## Key Concepts

### Routing Rules
- Rules are evaluated by priority (highest first)
- All conditions must match (AND logic)
- Actions are executed in order
- Rules can be dynamically added/updated/removed

### Condition Types
- **MESSAGE_CONTENT**: Check message text, speaker, etc.
- **USER_ATTRIBUTE**: Check user properties
- **CONTEXT_FIELD**: Check conversation metadata
- **ENTITY**: Check extracted entities
- **METADATA**: Check any metadata field
- **TIME_BASED**: Check time of day
- **TRIGGER**: Check handoff trigger results

### Action Types
- **ASSIGN_TO_AGENT**: Route to specific agent
- **ASSIGN_TO_QUEUE**: Route to queue
- **ASSIGN_TO_DEPARTMENT**: Route to department
- **SET_PRIORITY**: Set handoff priority
- **ADD_TAGS/REMOVE_TAGS**: Manage tags
- **SET_CUSTOM_FIELD**: Set custom fields
- **ROUTE_TO_FALLBACK**: Use fallback routing

## Documentation

For detailed documentation, see:
- [Routing Rules Guide](../docs/routing_rules_guide.md) - Comprehensive guide
- [Routing Rules Cheatsheet](../docs/routing_rules_cheatsheet.md) - Quick reference

## Examples by Use Case

### Customer Tier Routing
```python
# VIP → Senior Agent
# Premium → Priority Queue
# Standard → General Queue
```

### Issue Type Routing
```python
# Billing keywords → Billing Queue
# Technical errors → Tech Department
# Account issues → Account Queue
```

### Priority Escalation
```python
# Negative sentiment → Escalation
# Multiple failures → Senior Agent
# Contains "urgent" → High Priority
```

### Advanced Patterns
```python
# Multi-condition rules
# Regex pattern matching
# Time-based routing
# Negation rules
# Entity-based routing
```

## Best Practices

1. **Use meaningful rule names** that describe the purpose
2. **Set appropriate priorities** (100-1000 range)
3. **Add metadata** for documentation
4. **Test rules** before deployment
5. **Monitor performance** with profiling tools
6. **Use caching** for better performance

## Performance

- Rules evaluate in <100ms
- Caching available for repeated evaluations
- Async/await for non-blocking operations
- Priority-based evaluation for efficiency

## Need Help?

- Check the [main documentation](../README.md)
- Review the [routing rules guide](../docs/routing_rules_guide.md)
- Look at the examples in this directory
- Run the standalone test to verify functionality