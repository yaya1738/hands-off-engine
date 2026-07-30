from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

source = inspect.getsource(r.execute)

print("improvement_pipeline" in source)
print("improvement_executor.execute" in source)
print("trigger_improvement_pipeline" in source)
