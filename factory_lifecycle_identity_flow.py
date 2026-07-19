from ai.factory.runtime import FactoryRuntime

print("FACTORY IDENTITY FLOW PROBE")
print("=" * 45)

factory = FactoryRuntime()

result = factory.submit_development_request(
    "lifecycle trace test",
    "identity flow verification"
)

print("\nTOP LEVEL RESULT KEYS:")
print(list(result.keys()))

def walk(name, obj, depth=0):
    if depth > 3:
        return

    prefix = "  " * depth

    if isinstance(obj, dict):
        keys = list(obj.keys())

        interesting = [
            k for k in keys
            if any(
                x in k.lower()
                for x in [
                    "id",
                    "goal",
                    "task",
                    "artifact",
                    "change",
                    "status",
                    "approval",
                ]
            )
        ]

        if interesting:
            print(prefix + name, "=>", interesting)

        for k, v in obj.items():
            walk(k, v, depth + 1)

    elif isinstance(obj, list) and obj:
        walk(name + "[0]", obj[0], depth + 1)

walk("result", result)

print("\nHISTORY COUNTS")

for name, component in [
    ("goal", factory.goal_management),
    ("tracker", factory.development_tracker),
    ("approval", factory.improvement_approval),
    ("audit", factory.improvement_audit),
]:
    try:
        print(name, len(component.history()))
    except Exception:
        print(name, "no history")

print("\nDONE")
