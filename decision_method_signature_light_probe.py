import inspect
from ai.factory.decision_intelligence import FactoryDecisionIntelligence

print("DECISION SIGNATURES")
print("=" * 35)

obj = FactoryDecisionIntelligence()

for method in [
    "create_decision",
    "evaluate_options",
    "select_action",
]:
    fn = getattr(obj, method)
    print(method, ":", inspect.signature(fn))

print("DONE")
