import inspect
from ai.factory.runtime import FactoryRuntime

print(
    inspect.getsource(
        FactoryRuntime.run_autonomous_improvement
    )[-1200:]
)
