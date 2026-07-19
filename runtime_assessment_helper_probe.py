from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ASSESSMENT HELPERS")
print("=" * 30)

for name in dir(factory):
    if "metric" in name.lower() or "assessment" in name.lower():
        print(name)

print("DONE")
