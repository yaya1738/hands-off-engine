from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

print("EXECUTION SIGNATURES")
print("=" * 35)

for name in [
    "execute",
    "autonomous_execute",
    "execute_approved_improvement",
]:
    method = getattr(factory, name, None)
    if method:
        print(name, ":", inspect.signature(method))

print("DONE")
