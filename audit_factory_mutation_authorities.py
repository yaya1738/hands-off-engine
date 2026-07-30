import ast
from pathlib import Path

ROOT = Path("ai/factory")

keywords = [
    "create",
    "update",
    "save",
    "record",
    "execute",
    "approve",
    "resolve",
    "complete",
    "delete",
    "register",
]

for file in ROOT.glob("*.py"):
    try:
        tree = ast.parse(file.read_text())
    except:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name.lower()

            if any(k in name for k in keywords):
                print(
                    f"{file.name}: {node.lineno}: {node.name}"
                )
