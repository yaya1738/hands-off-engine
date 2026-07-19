from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

trace = factory.lifecycle_trace.trace()

plan = factory.improvement_planner.plan(trace)

print("FACTORY PLAN TASK CHECK")
print("=" * 35)

print("TASK COUNT:", len(plan.get("tasks", [])))
print("COMPONENT COUNT:", len(plan.get("components", [])))
print("VALIDATION COUNT:", len(plan.get("validation", [])))

print("DONE")
