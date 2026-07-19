from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

factory.submit_development_request(
    "lifecycle signal test",
    "trace"
)

sources = {
    "goal": factory.goal_management.history()[-1],
    "task": factory.development_tracker.history()[-1],
    "approval": factory.improvement_approval.history()[-1],
    "audit": factory.improvement_audit.history()[-1],
}

ignore = {
    "runtime",
    "factory",
    "components",
    "governance",
    "state",
    "events",
    "registry",
    "manager",
    "engine",
}

def extract(obj, path=""):
    found = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(x in k.lower() for x in ignore):
                continue

            if isinstance(v, (str, int, float, bool)):
                found.setdefault(k, []).append(v)

            elif isinstance(v, dict):
                found.update(extract(v, path + "." + k))

    return found


print("FACTORY LIFECYCLE SIGNALS")
print("=" * 35)

signals = {}

for name, record in sources.items():
    signals[name] = extract(record)
    print("\n", name.upper())
    print(sorted(signals[name].keys()))

print("\nPOTENTIAL JOIN FIELDS")
print("=" * 35)

names = list(signals)

for i in range(len(names)):
    for j in range(i+1, len(names)):
        a = names[i]
        b = names[j]

        shared = set(signals[a]) & set(signals[b])

        if shared:
            print(a, "<->", b, ":", sorted(shared))

print("\nDONE")
