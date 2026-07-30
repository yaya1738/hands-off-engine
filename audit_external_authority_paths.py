import ast
from pathlib import Path

FILES = [
    "autonomous_loop.py",
    "job_runner.py",
    "external_interface.py",
    "development_orchestrator.py",
    "intelligence_coordinator.py",
    "authority_gateway.py",
]

for filename in FILES:
    path = Path("ai/factory") / filename

    if not path.exists():
        continue

    tree = ast.parse(path.read_text())

    print("\n====", filename, "====")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):

                obj = node.func.value

                if isinstance(obj, ast.Attribute):
                    target = (
                        obj.attr
                        + "."
                        + node.func.attr
                    )

                    if any(x in target for x in [
                        "execute",
                        "approve",
                        "decide",
                        "create",
                        "update",
                        "record",
                    ]):
                        print(
                            node.lineno,
                            target
                        )
