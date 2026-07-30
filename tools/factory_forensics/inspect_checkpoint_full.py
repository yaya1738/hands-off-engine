from ai.factory.runtime import FactoryRuntime
import inspect

source = inspect.getsource(
    FactoryRuntime.run_checkpoint_cycle
)

print(source)
