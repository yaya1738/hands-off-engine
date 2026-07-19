from pathlib import Path
import ast
import json

ROOT = Path("ai/factory")
OUTPUT = Path("factory_reporting_capability_discovery.json")

KEYWORDS = [
    "report",
    "summary",
    "dashboard",
    "observability",
    "analytics",
    "status",
    "history",
]


def scan(path):
    result = {
        "file": str(path),
        "classes": [],
        "methods": [],
        "matches": [],
    }

    try:
        tree = ast.parse(path.read_text())
    except Exception as e:
        result["error"] = str(e)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)

        if isinstance(node, ast.FunctionDef):
            result["methods"].append(node.name)

            name = node.name.lower()

            for word in KEYWORDS:
                if word in name:
                    result["matches"].append(
                        {
                            "name": node.name,
                            "keyword": word,
                        }
                    )

    return result


def main():
    results = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            item = scan(path)
            if item["matches"]:
                results.append(item)

    output = {
        "existing_reporting_candidates": results,
        "count": len(results),
    }

    OUTPUT.write_text(
        json.dumps(output, indent=2)
    )

    print(json.dumps(output, indent=2)[:5000])


if __name__ == "__main__":
    main()
