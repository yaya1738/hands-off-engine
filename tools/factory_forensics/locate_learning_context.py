from ai.factory.runtime import FactoryRuntime
import inspect

source = inspect.getsource(FactoryRuntime)

lines = source.splitlines()

for n in range(975, 1000):
    if n <= len(lines):
        print(f"{n}: {lines[n-1]}")
