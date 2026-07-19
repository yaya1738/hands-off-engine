from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "planner option shape test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

plan = factory.improvement_planner.plan(trace)

print("PLANNER OPTION SHAPE")
print("=" * 35)

for key, value in plan.items():
    print(key, "=>", type(value).__name__)

print("DONE")
