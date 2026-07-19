from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

print("APPROVAL CONTRACT")
print("=" * 30)

approval = factory.improvement_approval

print("TYPE:", type(approval).__name__)

for name in [
    "approve",
    "request_approval",
    "submit",
    "review",
]:
    method = getattr(approval, name, None)
    if method:
        print(name, inspect.signature(method))

print("DONE")
