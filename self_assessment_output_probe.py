from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

assessment = factory.improvement_assessment.assess()

print("SELF ASSESSMENT OUTPUT")
print("=" * 35)

print("TYPE:", type(assessment).__name__)

if isinstance(assessment, dict):
    print("KEYS:", list(assessment.keys()))

print("DONE")
