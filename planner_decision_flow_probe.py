from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "planner decision flow test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

plan = factory.improvement_planner.plan(trace)

decision = factory.decision.create_decision(trace)

print("PLANNER → DECISION FLOW")
print("=" * 35)

try:
    evaluated = factory.decision.evaluate_options(
        decision,
        plan
    )

    print("EVALUATION: SUCCESS")
    print("TYPE:", type(evaluated).__name__)

except Exception as exc:
    print("EVALUATION: FAILED")
    print(type(exc).__name__)
    print(str(exc))

print("DONE")
