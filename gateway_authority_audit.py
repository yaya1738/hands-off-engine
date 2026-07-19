from pathlib import Path
import ast

path = Path("ai/factory/authority_gateway.py")

tree = ast.parse(path.read_text())

print("GATEWAY AUTHORITY AUDIT")
print("=" * 30)

for node in ast.walk(tree):

    # Find self.x = Something()
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    name = target.attr

                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            print(
                                "LOCAL CONSTRUCTION:",
                                name,
                                "->",
                                node.value.func.id
                            )

                        elif isinstance(node.value.func, ast.Attribute):
                            print(
                                "LOCAL CALL ASSIGN:",
                                name,
                                "->",
                                node.value.func.attr
                            )

    # Find methods
    if isinstance(node, ast.FunctionDef):
        print("METHOD:", node.name)

print()
print("CHECK COMPLETE")
