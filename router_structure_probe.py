from pathlib import Path
import ast

path = Path("ai/factory/action_router.py")

tree = ast.parse(path.read_text())

print("ACTION ROUTER STRUCTURE")
print("=" * 35)

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print("CLASS:", node.name)
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                print(" METHOD:", item.name)

    elif isinstance(node, ast.FunctionDef):
        print("FUNCTION:", node.name)

print("\nSOURCE:")
print(path.read_text()[:2000])
