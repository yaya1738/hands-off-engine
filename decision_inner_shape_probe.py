from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "decision inner shape test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

result = factory.decision.create_decision(trace)

inner = result.get("decision", {})

print("DECISION INNER CONTRACT")
print("=" * 35)

for key, value in inner.items():
    print(
        key,
        "=>",
        type(value).__name__
    )

print("DONE")
