from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

executor = factory.improvement_executor

print("FINAL EXECUTOR CONTRACT")
print("=" * 35)

print("TYPE:", type(executor).__name__)

for name in ["execute"]:
    method = getattr(executor, name, None)
    if method:
        print(name, inspect.signature(method))

print("DONE")
