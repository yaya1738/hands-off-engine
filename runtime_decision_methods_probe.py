from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("RUNTIME DECISION METHODS")
print("=" * 35)

for name in dir(factory):
    if "decision" in name.lower():
        print(name)

print("DONE")
