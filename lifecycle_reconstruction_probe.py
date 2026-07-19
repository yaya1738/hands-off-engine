from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "lifecycle reconstruction test",
    "trace"
)

print("LIFECYCLE RECONSTRUCTION")
print("=" * 35)

sources = [
    ("GOAL", factory.goal_management.history()),
    ("TRACKER", factory.development_tracker.history()),
    ("APPROVAL", factory.improvement_approval.history()),
    ("AUDIT", factory.improvement_audit.history()),
]

for name, history in sources:
    print("\n", name)
    if not history:
        print("EMPTY")
        continue

    item = history[-1]

    print("KEYS:", list(item.keys()))

    for key, value in item.items():
        if isinstance(value, dict):
            print(key, "->", list(value.keys()))

print("\nDONE")
