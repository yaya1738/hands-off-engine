from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print(inspect.signature(r.improvement_orchestrator.run_cycle))
print(inspect.getsource(r.improvement_orchestrator.run_cycle))
