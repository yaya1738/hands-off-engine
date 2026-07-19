from pathlib import Path
import ast
import json


TARGET = Path("ai/factory/runtime.py")
OUTPUT = Path("factory_runtime_report_signatures.json")


METHODS = [
    "factory_report",
    "integrity_report",
    "maintenance_status",
    "operator_status",
    "trend_report",
    "history",
]


def discover():
    result = {
        "class": "FactoryRuntime",
        "methods": {},
    }

    tree = ast.parse(
        TARGET.read_text()
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name in METHODS:

                args = []

                for arg in node.args.args:
                    args.append(
                        arg.arg
                    )

                result["methods"][node.name] = {
                    "arguments": args,
                    "line": node.lineno,
                }

    return result


def main():
    result = discover()

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
