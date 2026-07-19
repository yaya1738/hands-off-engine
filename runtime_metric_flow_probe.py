from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME METRIC FLOW")
print("=" * 35)

before = len(factory.observability.metrics)

factory.execute(
    {
        "objective": "metric flow test"
    }
)

after = len(factory.observability.metrics)

print("BEFORE:", before)
print("AFTER:", after)

print("DONE")
