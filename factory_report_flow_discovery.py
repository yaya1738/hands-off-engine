from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")
OUTPUT = Path("factory_report_flow_discovery.json")

TARGETS = [
    "factory_report",
    "integrity_report",
    "maintenance_status",
    "operator_status",
    "dashboard",
    "status",
    "history",
]


def inspect_file(path):
    result = {
        "file": str(path),
        "calls_found": [],
        "methods": [],
    }

    try:
        tree = ast.parse(path.read_text())
    except Exception as e:
        result["error"] = str(e)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            result["methods"].append(node.name)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr

                if name in TARGETS:
                    result["calls_found"].append(
                        name
                    )

    return result


def main():
    results = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            item = inspect_file(path)

            if item["calls_found"]:
                results.append(item)

    output = {
        "report_flow_candidates": results,
        "count": len(results),
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
        )
    )

    print(
        json.dumps(
            output,
            indent=2,
        )[:5000]
    )


if __name__ == "__main__":
    main()
