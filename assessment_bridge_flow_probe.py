from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.execute(
    {
        "objective": "assessment bridge verification"
    }
)

metrics = factory.get_assessment_metrics()

gaps = factory.improvement_assessment.detect_gaps(metrics)

print("ASSESSMENT BRIDGE FLOW")
print("=" * 35)
print("METRICS:", metrics)
print("GAPS TYPE:", type(gaps).__name__)
print("GAPS COUNT:", len(gaps))
print("DONE")
