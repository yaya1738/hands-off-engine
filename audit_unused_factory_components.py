import ast
from pathlib import Path

runtime = Path("ai/factory/runtime.py").read_text()

tree = ast.parse(runtime)

assigned = set()
called = set()

for node in ast.walk(tree):

    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                assigned.add(target.attr)

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            called.add(node.func.value.id if isinstance(node.func.value, ast.Name) else "")

print("ASSIGNED COMPONENTS")
for x in sorted(assigned):
    print(x)

print("\nDIRECT OBJECT CALLS")
for x in sorted(called):
    print(x)

print("\nPOTENTIAL UNUSED")
for x in sorted(assigned - called):
    print(x)
