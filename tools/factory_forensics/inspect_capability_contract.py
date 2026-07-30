from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

registry = r.improvement_capability_registry

print(inspect.getsource(registry.register))
print("----")
print(inspect.getsource(registry.resolve))
