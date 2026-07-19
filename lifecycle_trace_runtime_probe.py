from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME LIFECYCLE TRACE")
print("=" * 30)

print(
    "TRACE AVAILABLE:",
    hasattr(factory, "lifecycle_trace")
)

print(
    "TRACE TYPE:",
    type(factory.lifecycle_trace).__name__
    if hasattr(factory, "lifecycle_trace")
    else "MISSING"
)

print("DONE")
