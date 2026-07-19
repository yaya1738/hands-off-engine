from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

component = factory.adaptive_decision

print("ADAPTIVE DECISION COMPONENT")
print("=" * 35)

print("TYPE:", type(component).__name__)

for name in dir(component):
    if not name.startswith("_"):
        print(name)

print("DONE")
