from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("EXECUTION ACTION CONSUMERS")
print("=" * 35)

for name in dir(factory):
    if any(x in name.lower() for x in [
        "execute",
        "action",
        "approval",
        "improvement"
    ]):
        if not name.startswith("_"):
            print(name)

print("DONE")
