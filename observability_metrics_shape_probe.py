from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

metrics = factory.observability.metrics

print("OBSERVABILITY METRICS SHAPE")
print("=" * 35)

print("TYPE:", type(metrics).__name__)
print("COUNT:", len(metrics))

if metrics:
    print("FIRST TYPE:", type(metrics[0]).__name__)

print("DONE")
