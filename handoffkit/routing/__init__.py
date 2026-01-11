"""HandoffKit Routing Module.

Contains agent router and routing strategies.
"""

from handoffkit.routing.router import AgentRouter
from handoffkit.routing.strategies import (
    BaseStrategy,
    LeastBusyStrategy,
    RoundRobinStrategy,
    SkillBasedStrategy,
)

# Rule-based routing components
from handoffkit.routing.engine import RoutingEngine
from handoffkit.routing.models import RoutingRule, RoutingResult, RoutingConfig
from handoffkit.routing.conditions import Condition
from handoffkit.routing.actions import RuleAction
from handoffkit.routing.types import (
    RuleActionType,
    ConditionType,
    Operator,
    TimeUnit,
)

__all__ = [
    # Core routing
    "AgentRouter",
    "BaseStrategy",
    "RoundRobinStrategy",
    "LeastBusyStrategy",
    "SkillBasedStrategy",
    # Rule-based routing
    "RoutingEngine",
    "RoutingRule",
    "RoutingResult",
    "RoutingConfig",
    "Condition",
    "RuleAction",
    "RuleActionType",
    "ConditionType",
    "Operator",
    "TimeUnit",
]
