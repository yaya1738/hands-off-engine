from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME METRIC BRIDGE")
print("=" * 30)

print(
    "HAS:",
    hasattr(factory, "record_execution_metric")
)

print("DONE")
