from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ASSESSMENT METRIC BRIDGE")
print("=" * 35)

metrics = factory.get_assessment_metrics()

print("TYPE:", type(metrics).__name__)
print("VALUE:", metrics)

print("DONE")
