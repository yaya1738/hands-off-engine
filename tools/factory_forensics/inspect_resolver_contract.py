from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

resolver = r.improvement_action_resolver

print(inspect.getsource(resolver.resolve))
print("----")
print(inspect.getsource(resolver.register_action))
