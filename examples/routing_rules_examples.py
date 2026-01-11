#!/usr/bin/env python3
"""
Routing Rule Examples

This file contains comprehensive examples of routing rules that can be created
using the HandoffKit routing system. These examples demonstrate various
use cases and advanced features.
"""

from handoffkit.routing import (
    RoutingRule,
    RuleAction,
    Condition,
    RoutingConfig,
    RuleActionType,
    ConditionType,
    Operator,
)


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
        ],
        metadata={
            "description": "Route billing-related issues to billing support queue",
            "tags": ["finance", "billing"],
        }
    )

    # Example 2: Technical support routing
    technical_rule = RoutingRule(
        name="technical_support",
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
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "MEDIUM"}
            )
        ],
        metadata={
            "description": "Route technical errors to technical support department",
            "tags": ["technical", "error"],
        }
    )

    # Example 3: VIP customer routing
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
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["vip", "premium"]}
            )
        ],
        metadata={
            "description": "Route VIP customers to senior agents with high priority",
            "tags": ["vip", "premium"],
        }
    )

    return [billing_rule, technical_rule, vip_rule]


def create_advanced_routing_examples() -> list[RoutingRule]:
    """Create advanced routing rule examples."""

    # Example 1: Complex multi-condition rule
    complex_rule = RoutingRule(
        name="urgent_billing_vip",
        priority=300,  # Very high priority
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
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["vip", "billing", "urgent"]}
            )
        ],
        metadata={
            "description": "Urgent billing issues from VIP customers",
            "tags": ["vip", "billing", "urgent"],
        }
    )

    # Example 2: Time-based routing
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
            ),
            RuleAction(
                type=RuleActionType.SET_CUSTOM_FIELD,
                parameters={"field_name": "business_hours", "field_value": "after_hours"}
            )
        ],
        metadata={
            "description": "Route after-hours requests to special queue",
            "tags": ["time-based", "after-hours"],
        }
    )

    # Example 3: Sentiment-based routing
    negative_sentiment_rule = RoutingRule(
        name="negative_sentiment_escalation",
        priority=150,
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
                parameters={"tags": ["negative_sentiment", "escalation"]}
            )
        ],
        metadata={
            "description": "Escalate conversations with negative sentiment",
            "tags": ["sentiment", "escalation"],
        }
    )

    # Example 4: Entity-based routing
    product_issue_rule = RoutingRule(
        name="specific_product_issues",
        priority=110,
        conditions=[
            {
                "type": ConditionType.ENTITY,
                "field": "product_name",
                "operator": Operator.EQUALS,
                "value": "PremiumWidget"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_AGENT,
                parameters={"agent_id": "product-specialist-001"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["premium_widget", "product_issue"]}
            )
        ],
        metadata={
            "description": "Route PremiumWidget issues to product specialist",
            "tags": ["product", "specialist"],
        }
    )

    return [complex_rule, after_hours_rule, negative_sentiment_rule, product_issue_rule]


def create_regex_pattern_examples() -> list[RoutingRule]:
    """Create examples using regex patterns."""

    # Example 1: Order number pattern
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
        ],
        metadata={
            "description": "Detect and route messages with order numbers",
            "tags": ["regex", "order_number"],
        }
    )

    # Example 2: Email pattern detection
    email_mention_rule = RoutingRule(
        name="email_mention_detection",
        priority=85,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.REGEX_MATCHES,
                "value": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["email_mentioned"]}
            )
        ],
        metadata={
            "description": "Tag messages that contain email addresses",
            "tags": ["regex", "email"],
        }
    )

    # Example 3: Phone number detection
    phone_number_rule = RoutingRule(
        name="phone_number_detection",
        priority=86,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.REGEX_MATCHES,
                "value": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.SET_CUSTOM_FIELD,
                parameters={"field_name": "phone_detected", "field_value": True}
            )
        ],
        metadata={
            "description": "Detect phone numbers in messages",
            "tags": ["regex", "phone"],
        }
    )

    return [order_number_rule, email_mention_rule, phone_number_rule]


def create_negation_examples() -> list[RoutingRule]:
    """Create examples using negation."""

    # Example 1: Route non-English messages
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
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["non_english"]}
            )
        ],
        metadata={
            "description": "Route non-English messages to multilingual support",
            "tags": ["language", "negation"],
        }
    )

    # Example 2: Route issues not from web channel
    mobile_app_rule = RoutingRule(
        name="mobile_app_routing",
        priority=75,
        conditions=[
            {
                "type": ConditionType.CONTEXT_FIELD,
                "field": "channel",
                "operator": Operator.EQUALS,
                "value": "web",
                "negate": True
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "mobile_app_support"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["mobile_app"]}
            )
        ],
        metadata={
            "description": "Route non-web channel issues to mobile app support",
            "tags": ["mobile", "channel"],
        }
    )

    return [non_english_rule, mobile_app_rule]


def create_fallback_examples() -> list[RoutingRule]:
    """Create examples for fallback scenarios."""

    # Example 1: Route to fallback when no agents available
    no_agents_fallback = RoutingRule(
        name="no_agents_fallback",
        priority=50,
        conditions=[
            {
                "type": ConditionType.METADATA,
                "field": "agents_available",
                "operator": Operator.EQUALS,
                "value": False
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ROUTE_TO_FALLBACK,
                parameters={"reason": "no_agents_available"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "MEDIUM"}
            )
        ],
        metadata={
            "description": "Route to fallback when no agents are available",
            "tags": ["fallback", "availability"],
        }
    )

    return [no_agents_fallback]


def create_channel_specific_examples() -> list[RoutingRule]:
    """Create channel-specific routing examples."""

    # Example 1: Social media routing
    social_media_rule = RoutingRule(
        name="social_media_escalation",
        priority=160,
        conditions=[
            {
                "type": ConditionType.CONTEXT_FIELD,
                "field": "channel",
                "operator": Operator.IN_LIST,
                "value": ["twitter", "facebook", "instagram"]
            },
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "complaint"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_DEPARTMENT,
                parameters={"department": "social_media_team"}
            ),
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "HIGH"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["social_media", "complaint", "public"]}
            )
        ],
        metadata={
            "description": "Escalate social media complaints to social media team",
            "tags": ["social_media", "complaint", "escalation"],
        }
    )

    # Example 2: Voice call routing
    voice_call_rule = RoutingRule(
        name="voice_call_priority",
        priority=180,
        conditions=[
            {
                "type": ConditionType.CONTEXT_FIELD,
                "field": "channel",
                "operator": Operator.EQUALS,
                "value": "voice"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.SET_PRIORITY,
                parameters={"priority": "HIGH"}
            ),
            RuleAction(
                type=RuleActionType.ADD_TAGS,
                parameters={"tags": ["voice_call", "real_time"]}
            )
        ],
        metadata={
            "description": "Give priority to voice calls",
            "tags": ["voice", "priority"],
        }
    )

    return [social_media_rule, voice_call_rule]


def create_combined_configuration() -> RoutingConfig:
    """Create a complete routing configuration with all examples."""

    # Collect all rules
    all_rules = []
    all_rules.extend(create_basic_routing_examples())
    all_rules.extend(create_advanced_routing_examples())
    all_rules.extend(create_regex_pattern_examples())
    all_rules.extend(create_negation_examples())
    all_rules.extend(create_fallback_examples())
    all_rules.extend(create_channel_specific_examples())

    # Create configuration
    config = RoutingConfig(
        rules=all_rules,
        enable_caching=True,
        cache_ttl_seconds=300,
        max_evaluation_time_ms=100
    )

    return config


def print_rule_summary(rules: list[RoutingRule]) -> None:
    """Print a summary of the routing rules."""

    print("=== Routing Rules Summary ===\n")

    for rule in rules:
        print(f"Rule: {rule.name}")
        print(f"  Priority: {rule.priority}")
        print(f"  Enabled: {rule.is_enabled()}")
        print(f"  Conditions: {len(rule.conditions)}")
        print(f"  Actions: {len(rule.actions)}")
        if rule.metadata.description:
            print(f"  Description: {rule.metadata.description}")
        if rule.metadata.tags:
            print(f"  Tags: {', '.join(rule.metadata.tags)}")
        print()


def demonstrate_rule_usage() -> None:
    """Demonstrate how to use the routing rules."""

    print("=== Routing Rules Usage Examples ===\n")

    # Example 1: Create a simple configuration
    print("1. Creating a simple routing configuration:")
    basic_rules = create_basic_routing_examples()
    basic_config = RoutingConfig(rules=basic_rules)

    print(f"   Created configuration with {len(basic_config.rules)} rules\n")

    # Example 2: Add a new rule dynamically
    print("2. Adding a new rule dynamically:")
    new_rule = RoutingRule(
        name="custom_feedback_rule",
        priority=95,
        conditions=[
            {
                "type": ConditionType.MESSAGE_CONTENT,
                "field": "content",
                "operator": Operator.CONTAINS,
                "value": "feedback"
            }
        ],
        actions=[
            RuleAction(
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "feedback_team"}
            )
        ]
    )

    basic_config.add_rule(new_rule)
    print(f"   Added rule '{new_rule.name}'")
    print(f"   Total rules now: {len(basic_config.rules)}\n")

    # Example 3: Update an existing rule
    print("3. Updating an existing rule:")
    updated_rule = RoutingRule(
        name="billing_issues",
        priority=150,  # Increased priority
        conditions=[
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
                type=RuleActionType.ASSIGN_TO_QUEUE,
                parameters={"queue_name": "urgent_billing"}
            )
        ]
    )

    success = basic_config.update_rule("billing_issues", updated_rule)
    print(f"   Updated rule 'billing_issues': {success}\n")

    # Example 4: Disable a rule
    print("4. Disabling a rule:")
    rule_to_disable = basic_config.get_rule("technical_support")
    if rule_to_disable:
        rule_to_disable.disable()
        print(f"   Disabled rule 'technical_support'")
        print(f"   Rule enabled status: {rule_to_disable.is_enabled()}\n")

    # Example 5: Get configuration summary
    print("5. Configuration summary:")
    summary = basic_config.get_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    # Create and display examples
    print("HandoffKit Routing Rules Examples")
    print("=" * 50 + "\n")

    # Basic examples
    basic_rules = create_basic_routing_examples()
    print_rule_summary(basic_rules)

    # Advanced examples
    advanced_rules = create_advanced_routing_examples()
    print_rule_summary(advanced_rules)

    # Combined configuration
    full_config = create_combined_configuration()
    print(f"\nFull configuration created with {len(full_config.rules)} rules")

    # Demonstrate usage
    demonstrate_rule_usage()

    print("\n" + "=" * 50)
    print("Examples completed successfully!")
    print("\nKey takeaways:")
    print("- Rules can have multiple conditions (AND logic)")
    print("- Higher priority rules are evaluated first")
    print("- Rules can be dynamically added, updated, or disabled")
    print("- Each rule can have multiple actions")
    print("- Metadata helps organize and document rules")