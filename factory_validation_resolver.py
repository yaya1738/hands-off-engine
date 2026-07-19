from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")
OUTPUT = Path("factory_validation_plan.json")


WORDS = [
    "test",
    "validate",
    "check",
    "compile",
    "audit",
    "verify",
    "health",
    "integrity",
]


def scan_file(path):
    result = {
        "file": str(path),
        "classes": [],
        "methods": [],
        "validation_hooks": [],
    }

    try:
        tree = ast.parse(
            path.read_text()
        )
    except Exception as e:
        result["error"] = str(e)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result["classes"].append(
                node.name
            )

        if isinstance(node, ast.FunctionDef):
            result["methods"].append(
                node.name
            )

            name = node.name.lower()

            for word in WORDS:
                if word in name:
                    result["validation_hooks"].append(
                        {
                            "method": node.name,
                            "keyword": word,
                        }
                    )

    return result


def build_plan(results):
    hooks = []

    for item in results:
        if item.get("validation_hooks"):
            hooks.append(item)

    return {
        "validation_candidates": hooks,
        "candidate_count": len(hooks),
        "validation_required": True,
    }


def main():
    results = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            results.append(
                scan_file(path)
            )

    plan = build_plan(results)

    OUTPUT.write_text(
        json.dumps(
            plan,
            indent=2,
        )
    )

    print("Validation resolver complete")
    print(
        json.dumps(
            plan,
            indent=2,
        )[:5000]
    )


if __name__ == "__main__":
    main()
