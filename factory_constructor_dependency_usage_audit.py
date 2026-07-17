import ast
import json
from pathlib import Path


TARGET = Path("ai/factory/development_pipeline.py")
OUTPUT = Path("factory_constructor_dependency_usage.json")


DEPENDENCIES = [
    "advisor",
    "approval",
]


def main():
    tree = ast.parse(
        TARGET.read_text()
    )

    result = {
        "file": str(TARGET),
        "dependencies": {},
    }

    for dep in DEPENDENCIES:
        result["dependencies"][dep] = {
            "constructor_found": False,
            "references": [],
        }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "__init__":
                args = [
                    arg.arg
                    for arg in node.args.args
                ]

                for dep in DEPENDENCIES:
                    if dep in args:
                        result["dependencies"][dep]["constructor_found"] = True

        if isinstance(node, ast.Attribute):
            if node.attr in DEPENDENCIES:
                result["dependencies"][node.attr]["references"].append(
                    {
                        "line": node.lineno,
                        "attribute": node.attr,
                    }
                )

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
