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
}

options = adapter.build_options(plan)

result = decision.select_action(options)

print("SELECTED ACTION SHAPE")
print("=" * 30)

print("TYPE:", type(result).__name__)

if isinstance(result, dict):
    print("KEYS:", list(result.keys()))

print("DONE")
