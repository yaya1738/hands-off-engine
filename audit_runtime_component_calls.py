import ast
from pathlib import Path

runtime = Path("ai/factory/runtime.py").read_text()
tree = ast.parse(runtime)

objects = []

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    objects.append(target.attr)

objects = sorted(set(objects))

usage = {obj: [] for obj in objects}

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func = node.func

        if isinstance(func, ast.Attribute):
            value = func.value

            if isinstance(value, ast.Attribute):
                if (
                    isinstance(value.value, ast.Name)
                    and value.value.id == "self"
                ):
                    obj = value.attr
                    if obj in usage:
                        usage[obj].append(func.attr)

for obj in objects:
    calls = sorted(set(usage[obj]))

    if calls:
        print(f"{obj}:")
        for c in calls:
            print(f"  - {c}")
    else:
        print(f"{obj}: NO_DIRECT_CALLS")
