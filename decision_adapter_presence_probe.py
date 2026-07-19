from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("DECISION ADAPTER CHECK")
print("=" * 30)

found = []

for name in dir(factory):
    if "adapter" in name.lower() or "bridge" in name.lower():
        found.append(name)

print("FOUND:", found if found else "NONE")

print("DONE")
