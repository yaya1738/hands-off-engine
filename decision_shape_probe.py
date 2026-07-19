from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "decision shape test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

decision = factory.decision.create_decision(trace)

print("DECISION SHAPE")
print("=" * 25)

print("TYPE:", type(decision).__name__)

if isinstance(decision, dict):
    print("KEYS:", list(decision.keys()))

    for k, v in decision.items():
        print(k, "=>", type(v).__name__)

print("DONE")
