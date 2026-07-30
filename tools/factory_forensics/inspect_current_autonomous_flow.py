from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print(inspect.getsource(r.run_autonomous_improvement))
