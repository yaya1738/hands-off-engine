from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("DECISION OPTION CAPABILITY")
print("=" * 35)

for name in dir(factory):
    if any(x in name.lower() for x in [
        "option",
        "recommend",
        "plan",
        "strategy",
        "proposal",
    ]):
        print(name)

print("DONE")
