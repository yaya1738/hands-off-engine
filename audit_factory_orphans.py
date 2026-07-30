import ast
from pathlib import Path
from collections import defaultdict

runtime = Path("ai/factory/runtime.py").read_text()

objects = []

tree = ast.parse(runtime)

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.attr not in ["_history"]:
                    objects.append(target.attr)

for obj in sorted(set(objects)):
    used = 0

    for file in Path("ai/factory").rglob("*.py"):
        if file.name == "runtime.py":
            continue

        try:
            text = file.read_text()
        except:
            continue

        if obj in text:
            used += 1

    if used == 0:
        print(obj)

print("TOTAL_RUNTIME_OBJECTS:", len(set(objects)))
