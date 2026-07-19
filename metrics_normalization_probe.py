from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

obs = factory.observability

print("METRIC NORMALIZATION CHECK")
print("=" * 35)

for name in dir(obs):
    if not name.startswith("_"):
        if "metric" in name.lower() or "health" in name.lower():
            print(name)

print("DONE")
