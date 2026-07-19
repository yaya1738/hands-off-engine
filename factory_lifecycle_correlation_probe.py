from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

result = factory.submit_development_request(
    "correlation probe",
    "factory lifecycle analysis"
)

print("FACTORY LIFECYCLE CORRELATION")
print("=" * 40)

records = {
    "goal": factory.goal_management.history(),
    "task": factory.development_tracker.history(),
    "approval": factory.improvement_approval.history(),
    "audit": factory.improvement_audit.history(),
}

def flatten(obj):
    found = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict):
                found.update(flatten(v))
            elif isinstance(v, (str, int)):
                found.setdefault(k, []).append(v)
    return found

snapshots = {}

for name, history in records.items():
    if history:
        snapshots[name] = flatten(history[-1])

for a, av in snapshots.items():
    print("\n", a.upper())

    matches = []

    for b, bv in snapshots.items():
        if a == b:
            continue

        shared = set(av.keys()) & set(bv.keys())

        for key in shared:
            if set(map(str, av[key])) & set(map(str, bv[key])):
                matches.append(key)

    print("LINK KEYS:", sorted(set(matches)))

print("\nFACTORY COMPONENT INTELLIGENCE:")
print("CHANGE IMPACT:", factory.change_impact_report({
    "type": "lifecycle_trace_probe"
}))

print("\nDONE")
