from ai.factory.runtime import FactoryRuntime
import inspect

runtime = FactoryRuntime()

print(inspect.getsource(
    runtime.execute_approved_improvement
))

print("----")

print(inspect.getsource(
    runtime.process_approved_improvement
))
