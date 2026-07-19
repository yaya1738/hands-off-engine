from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")
OUTPUT = Path("factory_execution_integration_discovery.json")


TARGET_WORDS = [
    "execute",
    "run",
    "submit",
    "request",
    "improvement",
    "pipeline",
    "task",
    "job",
    "dispatch",
    "orchestr",
]


def inspect_file(path):
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

            for word in TARGET_WORDS:
                if word in name:
                    result["matches"].append(
                        {
                            "type": "method",
                            "name": node.name,
                            "keyword": word,
                        }
                    )

    return result


def main():
    results = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            results.append(
                inspect_file(path)
            )

    report = {
        "files_scanned": len(results),
        "execution_candidates": [
            item
            for item in results
            if item.get("matches")
        ],
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
        )
    )

    print("Execution integration discovery complete")
    print(
        json.dumps(
            report,
            indent=2,
        )[:5000]
    )


if __name__ == "__main__":
    main()
