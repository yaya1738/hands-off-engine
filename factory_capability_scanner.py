from pathlib import Path
import ast
import json


ROOT = Path("ai/factory")


KEYWORDS = {
    "diagnostic": [],
    "inspect": [],
    "audit": [],
    "registry": [],
    "graph": [],
    "dependency": [],
    "orchestr": [],
    "scheduler": [],
    "executor": [],
    "runtime": [],
    "health": [],
}


def scan_file(path):
    result = {
        "file": str(path),
        "classes": [],
        "functions": [],
        "imports": [],
        "capabilities": [],
    }

    try:
        tree = ast.parse(path.read_text())
    except Exception as e:
        result["error"] = str(e)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)

        elif isinstance(node, ast.FunctionDef):
            result["functions"].append(node.name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            result["imports"].append(
                ast.unparse(node)
            )

    text = path.read_text().lower()

    for keyword in KEYWORDS:
        if keyword in text:
            result["capabilities"].append(keyword)

    return result


def classify(results):
    summary = {
        "files_scanned": len(results),
        "capabilities_found": {},
        "components": [],
    }

    for item in results:
        summary["components"].extend(
            item["classes"]
        )

        for capability in item["capabilities"]:
            summary["capabilities_found"].setdefault(
                capability,
                []
            ).append(item["file"])

    return summary


def main():
    results = []

    for path in ROOT.rglob("*.py"):
        if "__pycache__" not in str(path):
            results.append(
                scan_file(path)
            )

    report = {
        "files": results,
        "summary": classify(results),
    }

    Path("factory_capability_report.json").write_text(
        json.dumps(
            report,
            indent=2,
        )
    )

    print(
        "Capability scan complete"
    )
    print(
        json.dumps(
            report["summary"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
