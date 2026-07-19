from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

obs = factory.observability

print("OBSERVABILITY CONTRACT")
print("=" * 35)

print("TYPE:", type(obs).__name__)

for name in dir(obs):
    if not name.startswith("_"):
        print(name)

print("DONE")
