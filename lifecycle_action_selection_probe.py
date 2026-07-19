from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "lifecycle action selection test",
    "factory"
)

trace = factory.lifecycle_trace.trace()

decision = factory.decision.create_decision(trace)

action = factory.decision.select_action(decision)

print("LIFECYCLE ACTION SELECTION")
print("=" * 35)

print(
    "ACTION GENERATED:",
    "YES" if action is not None else "NO"
)

print(
    "ACTION TYPE:",
    type(action).__name__
)

print("DONE")
