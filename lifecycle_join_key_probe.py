from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "join key test",
    "trace"
)

print("LIFECYCLE JOIN KEYS")
print("=" * 30)

for name, history in [
    ("GOAL", factory.goal_management.history()),
    ("TRACKER", factory.development_tracker.history()),
    ("APPROVAL", factory.improvement_approval.history()),
    ("AUDIT", factory.improvement_audit.history()),
]:
    print("\n", name)

    if not history:
        print("EMPTY")
        continue

    item = history[-1]

    def show(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(
                    x in k.lower()
                    for x in ["id", "task", "goal", "objective", "type"]
                ):
                    print(prefix + k, "=", v if not isinstance(v, dict) else list(v.keys()))
                if isinstance(v, dict):
                    show(v, prefix+"  ")

    show(item)

print("\nDONE")
