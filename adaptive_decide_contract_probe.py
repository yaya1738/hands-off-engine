from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

method = factory.adaptive_decision.decide

print("ADAPTIVE DECIDE CONTRACT")
print("=" * 35)

print("CALLABLE:", callable(method))
print("TYPE:", type(method).__name__)

print("ATTRIBUTES:")
for name in dir(method):
    if not name.startswith("_"):
        print(name)

print("DONE")
