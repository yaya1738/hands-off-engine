from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print({
    "execute_source": inspect.getsource(r.execute),
    "has_improvement_executor": hasattr(r, "improvement_executor"),
    "executor_type": type(r.improvement_executor).__name__
})
