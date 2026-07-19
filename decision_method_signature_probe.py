from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

print("DECISION SIGNATURES")
print("=" * 35)

for method in [
    "create_decision",
    "evaluate_options",
    "select_action",
]:
    fn = getattr(factory.decision, method)
    print(method, ":", inspect.signature(fn))

print("DONE")
