from ai.factory.runtime import FactoryRuntime
import inspect

source = inspect.getsource(
    FactoryRuntime.run_checkpoint_cycle
)

for i, line in enumerate(source.splitlines(), 1):
    if "return" in line or "result" in line or "execute" in line:
        print(f"{i}: {line.strip()}")
