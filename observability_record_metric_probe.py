from ai.factory.runtime import FactoryRuntime
import inspect

factory = FactoryRuntime()

print("RECORD METRIC CONTRACT")
print("=" * 35)

method = factory.observability.record_metric

print("CALLABLE:", callable(method))

try:
    print("SIGNATURE:", inspect.signature(method))
except Exception as e:
    print("SIGNATURE ERROR:", type(e).__name__)

print("DONE")
