import ai.factory.decision_intelligence as d

print("DECISION MODULE CHECK")
print("=" * 30)

found = []

for name in dir(d):
    if "adapter" in name.lower() or "bridge" in name.lower():
        found.append(name)

print("FOUND:", found if found else "NONE")

print("DONE")
