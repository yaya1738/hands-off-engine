from ai.factory.runtime import FactoryRuntime
from pathlib import Path
import ast


runtime = FactoryRuntime()

authority_map = runtime.authority_map()

ownership = {}

for authority, components in authority_map.items():
    for component in components:
        ownership[component] = authority


def find_calls():

    calls = {}

    root = Path("ai/factory")

    for file in root.glob("*.py"):
        try:
            tree = ast.parse(file.read_text())
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    obj = node.value.id
                    calls.setdefault(obj, set()).add(node.attr)

    return calls


calls = find_calls()


print("\n==== AUTHORITY CAPABILITY MATRIX ====\n")

for name, authority in sorted(ownership.items()):

    exists = hasattr(runtime, name)

    methods = sorted(
        calls.get(name, [])
    )

    if not exists:
        status = "MISSING_RUNTIME"
    elif methods:
        status = "ACTIVE"
    else:
        status = "NO_DIRECT_CALLS"

    print(
        f"{name:35} | "
        f"{authority:20} | "
        f"{status:18} | "
        f"{methods}"
    )


print("\n==== UNASSIGNED RUNTIME OBJECTS ====\n")

for name in vars(runtime):
    if name not in ownership:
        print(name)
