# Routing Rules Quick Reference

## Common Rule Patterns

### 1. Customer Tier Routing
```python
# VIP Customers → Senior Agent
tier: "vip" → agent: "senior-agent-001" (priority: 200)

# Premium Customers → Priority Queue
tier: "premium" → queue: "priority_support" (priority: 150)

# Standard Customers → General Queue
tier: "standard" → queue: "general_support" (priority: 100)
```

### 2. Issue Type Routing
```python
# Billing Keywords → Billing Queue
["billing", "invoice", "payment"] → queue: "billing" (priority: 120)

# Technical Keywords → Tech Department
["error", "bug", "crash"] → department: "technical" (priority: 110)

# Account Keywords → Account Queue
["login", "password", "access"] → queue: "account_support" (priority: 115)
```

### 3. Priority Escalation
```python
# Negative Sentiment → Escalation
sentiment < 0.3 → department: "escalation" (priority: 250)

# Multiple Failures → Senior Agent
failures > 3 → agent: "senior-agent" (priority: 240)

# Contains "urgent" → High Priority
content contains "urgent" → priority: HIGH (priority: 130)
```

### 4. Time-Based Routing
```python
# After Hours → Special Queue
time after 18:00 → queue: "after_hours" (priority: 80)

# Weekends → Weekend Team
day in ["Saturday", "Sunday"] → queue: "weekend_team" (priority: 90)
```

### 5. Channel-Based Routing
```python
# Social Media Complaints → Social Team
channel in ["twitter", "facebook"] AND content contains "complaint"
→ department: "social_media" (priority: 160)

# Voice Calls → High Priority
channel: "voice" → priority: HIGH (priority: 180)
```

## Condition Operators

### String Operators
- `EQUALS` - Exact match (case-insensitive by default)
- `NOT_EQUALS` - Not equal
- `CONTAINS` - Contains substring
- `NOT_CONTAINS` - Does not contain
- `STARTS_WITH` - Starts with
- `ENDS_WITH` - Ends with
- `REGEX_MATCHES` - Matches regex pattern

### Numeric Operators
- `GREATER_THAN` - >
- `LESS_THAN` - <
- `GREATER_EQUAL` - >=
- `LESS_EQUAL` - <=
- `IN_RANGE` - Between two values [min, max]

### List Operators
- `IN_LIST` - Value in list
- `NOT_IN_LIST` - Value not in list

### Boolean Operators
- `IS_TRUE` - Is truthy
- `IS_FALSE` - Is falsy

### Existence Operators
- `EXISTS` - Field exists
- `NOT_EXISTS` - Field doesn't exist

### Time Operators
- `AFTER` - After time (HH:MM format)
- `BEFORE` - Before time (HH:MM format)
- `BETWEEN` - Between times [HH:MM, HH:MM]

## Action Types

### Assignment Actions
```python
# Assign to specific agent
RuleAction(RuleActionType.ASSIGN_TO_AGENT, {"agent_id": "agent-123"})

# Assign to queue
RuleAction(RuleActionType.ASSIGN_TO_QUEUE, {"queue_name": "billing"})

# Assign to department
RuleAction(RuleActionType.ASSIGN_TO_DEPARTMENT, {"department": "technical"})
```

### Priority Action
```python
# Set priority (LOW, MEDIUM, HIGH, URGENT, CRITICAL)
RuleAction(RuleActionType.SET_PRIORITY, {"priority": "HIGH"})
```

### Tag Actions
```python
# Add tags
RuleAction(RuleActionType.ADD_TAGS, {"tags": ["billing", "urgent"]})

# Remove tags
RuleAction(RuleActionType.REMOVE_TAGS, {"tags": ["low_priority"]})
```

### Custom Field Action
```python
# Set custom field
RuleAction(RuleActionType.SET_CUSTOM_FIELD, {
    "field_name": "customer_type",
    "field_value": "enterprise"
})
```

### Fallback Action
```python
# Route to fallback
RuleAction(RuleActionType.ROUTE_TO_FALLBACK, {"reason": "no_agents"})
```

## Condition Types

### Message Content
```python
{
    "type": ConditionType.MESSAGE_CONTENT,
    "field": "content",  # content, speaker, timestamp, length
    "operator": Operator.CONTAINS,
    "value": "billing"
}
```

### User Attributes
```python
{
    "type": ConditionType.USER_ATTRIBUTE,
    "field": "tier",  # Any user attribute
    "operator": Operator.EQUALS,
    "value": "premium"
}
```

### Context Fields
```python
{
    "type": ConditionType.CONTEXT_FIELD,
    "field": "channel",  # channel, region, etc.
    "operator": Operator.EQUALS,
    "value": "web"
}
```

### Entities
```python
{
    "type": ConditionType.ENTITY,
    "field": "product_name",  # Entity type
    "operator": Operator.EQUALS,
    "value": "PremiumWidget"
}
```

### Metadata
```python
{
    "type": ConditionType.METADATA,
    "field": "sentiment_score",  # Any metadata field
    "operator": Operator.LESS_THAN,
    "value": 0.3
}
```

### Triggers
```python
{
    "type": ConditionType.TRIGGER,
    "field": "trigger_type",  # trigger_type, confidence, reason
    "operator": Operator.EQUALS,
    "value": "keyword_match"
}
```

### Time-Based
```python
{
    "type": ConditionType.TIME_BASED,
    "operator": Operator.AFTER,
    "value": "18:00"
}
```

## Priority Guidelines

- **Critical**: 800-1000 (VIP issues, escalations)
- **High**: 600-799 (Urgent issues, billing)
- **Medium**: 400-599 (Standard issues)
- **Low**: 200-399 (Non-urgent, informational)
- **Fallback**: 1-199 (Catch-all rules)

## Quick Examples

### VIP + Billing + Urgent
```python
conditions=[
    {"field": "tier", "value": ["vip", "premium"], "operator": IN_LIST},
    {"field": "content", "value": "billing", "operator": CONTAINS},
    {"field": "content", "value": "urgent", "operator": CONTAINS}
],
actions=[
    {"type": ASSIGN_TO_AGENT, "agent_id": "senior-billing"},
    {"type": SET_PRIORITY, "priority": "CRITICAL"}
],
priority: 900
```

### Regex Pattern Detection
```python
conditions=[
    {"field": "content", "value": r"ORD-\d{8}", "operator": REGEX_MATCHES}
],
actions=[
    {"type": SET_CUSTOM_FIELD, "field_name": "has_order", "field_value": True},
    {"type": ASSIGN_TO_QUEUE, "queue_name": "order_support"}
],
priority: 120
```

### Sentiment-Based Escalation
```python
conditions=[
    {"field": "sentiment_score", "value": 0.3, "operator": LESS_THAN}
],
actions=[
    {"type": ASSIGN_TO_DEPARTMENT, "department": "escalation"},
    {"type": SET_PRIORITY, "priority": "HIGH"},
    {"type": ADD_TAGS, "tags": ["negative_sentiment"]}
],
priority: 250
```

## Performance Tips

1. **Order matters**: Place faster conditions first
2. **Use caching**: Enable with `enable_caching=True`
3. **Limit regex**: Expensive in high-traffic rules
4. **Priority wisely**: Higher priority = evaluated first
5. **Test performance**: Use `RulePerformanceProfiler`

## Common Mistakes to Avoid

1. **No priority spread**: All rules at same priority
2. **Too many conditions**: Max 20 per rule
3. **Expensive regex first**: Slows evaluation
4. **No metadata**: Makes rules hard to understand
5. **No testing**: Always test rules before deployment