from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

planner = factory.improvement_planner

print("PLANNER CONTRACT")
print("=" * 35)

print("TYPE:", type(planner).__name__)

for name in dir(planner):
    if not name.startswith("_"):
        print(name)

print("DONE")
