import ast
from pathlib import Path

ROOT = Path("ai/factory")

for file in ROOT.glob("*.py"):
    try:
        tree = ast.parse(file.read_text())
    except:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                chain = []

                obj = node.func.value

                if isinstance(obj, ast.Attribute):
                    chain.append(obj.attr)

                chain.append(node.func.attr)

                name = ".".join(chain)

                if any(x in name for x in [
                    "execute",
                    "approve",
                    "decide",
                    "record",
                    "complete",
                    "create",
                    "update",
                    "resolve",
                ]):
                    print(
                        f"{file.name}:{node.lineno}: {name}"
                    )
