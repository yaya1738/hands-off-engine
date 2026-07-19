from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "decision path test",
    "lifecycle"
)

trace = factory.lifecycle_trace.trace()

print("LIFECYCLE DECISION PATH")
print("=" * 35)

checks = [
    (
        "DECISION INTELLIGENCE",
        hasattr(factory, "decision")
    ),
    (
        "RECOMMENDATIONS",
        hasattr(factory, "recommendation_feedback")
    ),
    (
        "PLANNING",
        hasattr(factory, "planning")
    ),
    (
        "ORCHESTRATION",
        hasattr(factory, "orchestration")
    ),
    (
        "LIFECYCLE TRACE AVAILABLE",
        bool(trace.get("lifecycle_status"))
    ),
]

for name, value in checks:
    print(name + ":", "YES" if value else "NO")

print()
print("TRACE STATUS:", trace["lifecycle_status"])

print("DONE")
