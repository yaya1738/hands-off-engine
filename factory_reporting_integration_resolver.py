from pathlib import Path
import ast
import json


OUTPUT = Path("factory_reporting_integration_plan.json")
ROOT = Path("ai/factory")


TARGETS = [
    {
        "file": "runtime.py",
        "class": "FactoryRuntime",
        "preferred": [
            "factory_report",
            "integrity_report",
            "maintenance_status",
            "operator_status",
            "history",
        ],
    },
    {
        "file": "api.py",
        "class": "FactoryAPI",
        "preferred": [
            "dashboard",
            "status",
            "history",
        ],
    },
    {
        "file": "cli.py",
        "class": "FactoryCLI",
        "preferred": [
            "status",
            "history",
        ],
    },
]


def inspect_class(path, target_class):
    result = []

    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name == target_class:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        result.append(item.name)

    return result


def resolve():
    plan = {
        "selected_reporting_sources": [],
        "fallback_required": False,
    }

    for target in TARGETS:
        path = ROOT / target["file"]

        if not path.exists():
            continue

        methods = inspect_class(
            path,
            target["class"],
        )

        available = [
            method
            for method in target["preferred"]
            if method in methods
        ]

        if available:
            plan["selected_reporting_sources"].append(
                {
                    "component": target["class"],
                    "file": str(path),
                    "available_methods": available,
                }
            )

    if not plan["selected_reporting_sources"]:
        plan["fallback_required"] = True

    return plan


def main():
    result = resolve()

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
