from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

adapter = factory.decision_option_adapter

print("DECISION ADAPTER CONTRACT")
print("=" * 35)

print("TYPE:", type(adapter).__name__)

for name in dir(adapter):
    if not name.startswith("_"):
        if "build" in name.lower() or "option" in name.lower():
            print(name)

print("DONE")
