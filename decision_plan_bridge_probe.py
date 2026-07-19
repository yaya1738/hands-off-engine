from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

decision = factory.decision

print("DECISION BRIDGE METHODS")
print("=" * 35)

for name in dir(decision):
    if not name.startswith("_"):
        if any(x in name.lower() for x in [
            "plan",
            "option",
            "action",
            "create",
            "evaluate",
        ]):
            print(name)

print("DONE")
