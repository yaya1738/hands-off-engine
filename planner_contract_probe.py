from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "planner contract test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

print("PLANNER CONTRACT")
print("=" * 30)

plan = factory.improvement_planner.plan(trace)

print("TYPE:", type(plan).__name__)

if isinstance(plan, dict):
    print("KEYS:", list(plan.keys()))

print("DONE")
