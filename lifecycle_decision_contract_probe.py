from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "lifecycle decision contract test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

decision = factory.decision.create_decision(
    trace
)

print("LIFECYCLE DECISION CONTRACT")
print("=" * 35)

print("INPUT ACCEPTED: YES")

print(
    "DECISION TYPE:",
    type(decision).__name__
)

if isinstance(decision, dict):
    print(
        "DECISION STATUS:",
        decision.get("status", "none")
    )

print("DONE")
