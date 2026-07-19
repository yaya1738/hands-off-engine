from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("FACTORY DECISION CONTRACT")
print("=" * 35)

decision = factory.decision

print("METHODS:")

for name in dir(decision):
    if not name.startswith("_"):
        print(name)

print("DONE")
