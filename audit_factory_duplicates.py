from ai.factory.runtime import FactoryRuntime
from collections import defaultdict

r = FactoryRuntime()

groups = defaultdict(list)

for name, obj in vars(r).items():
    if obj is None:
        continue

    cls = type(obj).__name__

    groups[cls].append(name)

print("\n==== DUPLICATE IMPLEMENTATIONS ====\n")

for cls, names in sorted(groups.items()):
    if len(names) > 1:
        print(cls)
        for n in names:
            print("  -", n)

print("\n==== TOTAL COMPONENTS ====")
print(len(vars(r)))
