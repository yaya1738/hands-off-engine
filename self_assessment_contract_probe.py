from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

assessment = factory.improvement_assessment

print("SELF ASSESSMENT CONTRACT")
print("=" * 35)

print("TYPE:", type(assessment).__name__)

for name in dir(assessment):
    if not name.startswith("_"):
        print(name)

print("DONE")
