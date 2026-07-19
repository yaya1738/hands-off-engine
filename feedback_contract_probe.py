from ai.factory.runtime import FactoryRuntime
import inspect

runtime = FactoryRuntime()

print(inspect.signature(runtime.feedback_engine.analyze))
print(inspect.getsource(runtime.feedback_engine.analyze))
