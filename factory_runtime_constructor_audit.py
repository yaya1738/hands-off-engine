import ast
import json
from pathlib import Path


TARGET = Path("ai/factory/runtime.py")
OUTPUT = Path("factory_runtime_constructor_audit.json")


def main():
    tree = ast.parse(
        TARGET.read_text()
    )

    calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    name = node.value.func.id

                    if name.startswith("Factory"):
                        calls.append(
                            {
                                "class": name,
                                "line": node.lineno,
                                "keywords": [
                                    k.arg
                                    for k in node.value.keywords
                                ],
                            }
                        )

    result = {
        "runtime_constructor_calls": calls,
        "count": len(calls),
    }

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
