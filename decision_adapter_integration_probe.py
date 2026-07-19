from ai.factory.decision_intelligence import FactoryDecisionIntelligence
from ai.factory.decision_option_adapter import FactoryDecisionOptionAdapter

decision = FactoryDecisionIntelligence()
adapter = FactoryDecisionOptionAdapter()

plan = {
    "tasks": [
        "improve lifecycle routing",
        "validate execution path",
    ],
    "priority": 5,
    "context": "factory",
}

options = adapter.build_options(plan)

print("DECISION ADAPTER INTEGRATION")
print("=" * 35)

evaluated = decision.evaluate_options(options)

print("EVALUATED TYPE:", type(evaluated).__name__)

action = decision.select_action(options)

print("SELECTED TYPE:", type(action).__name__)
print("HAS ACTION:", isinstance(action, dict) and "action" in action)

print("DONE")
