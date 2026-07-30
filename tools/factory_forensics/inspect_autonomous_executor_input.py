from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print(inspect.signature(r.execute_autonomous_improvements))
print(inspect.getsource(r.execute_autonomous_improvements))
