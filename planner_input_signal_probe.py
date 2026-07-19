from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

trace = factory.lifecycle_trace.trace()

print("PLANNER INPUT SIGNAL")
print("=" * 35)

print("TRACE TYPE:", type(trace).__name__)

if isinstance(trace, dict):
    print("TRACE KEYS:", list(trace.keys()))

print("DONE")
