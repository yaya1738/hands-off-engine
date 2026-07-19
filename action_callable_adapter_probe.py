from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ACTION ADAPTER CHECK")
print("=" * 35)

for name in dir(factory):
    if "action" in name.lower() or "adapter" in name.lower():
        if not name.startswith("_"):
            print(name)

print("DONE")
