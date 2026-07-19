from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("FACTORY DECISION FLOW")
print("=" * 35)

trace = factory.lifecycle_trace.trace()

plan = factory.improvement_planner.plan(trace)

options = factory.decision_option_adapter.build_options(plan)

decision_result = factory.decision.evaluate_options(options)

print("PLAN:", bool(plan))
print("OPTIONS:", len(options))
print("DECISION TYPE:", type(decision_result).__name__)

print("DONE")
