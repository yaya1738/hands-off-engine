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

print("SELECTED VALUE")
print("=" * 25)

print("TYPE:", type(result.get("selected")).__name__)

if isinstance(result.get("selected"), dict):
    print("KEYS:", list(result["selected"].keys()))
else:
    print("VALUE:", result.get("selected"))

print("DONE")
