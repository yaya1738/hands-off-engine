import json
import subprocess
import ast
from pathlib import Path
from datetime import datetime, timezone


TARGET_WORDS = [
    "create",
    "build",
    "generate",
    "execute",
    "artifact",
    "develop",
    "write",
]


def get_capability_report():
    result = subprocess.run(
        ["python", "factory_capability_analyzer.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    output = result.stdout

    start = output.find("{")

    if start == -1:
        return {}

    return json.loads(output[start:])


def find_candidate_files(report):
    files = []

    for category in report.get("capabilities", {}).values():
        for file in category.get("files", []):
            if file not in files:
                files.append(file)

    return files


def inspect_file(path):
    score = 0
    methods = []

    try:
        source = Path(path).read_text(errors="ignore")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name.lower()
                methods.append(node.name)

                for word in TARGET_WORDS:
                    if word in name:
                        score += 2

            elif isinstance(node, ast.ClassDef):
                name = node.name.lower()

                for word in TARGET_WORDS:
                    if word in name:
                        score += 3

    except Exception:
        return {
            "file": path,
            "error": "inspection_failed",
            "score": 0,
        }

    return {
        "file": path,
        "score": score,
        "methods": methods[:20],
    }


def resolve():
    report = get_capability_report()

    candidates = find_candidate_files(report)

    inspected = [
        inspect_file(path)
        for path in candidates
    ]

    ranked = sorted(
        inspected,
        key=lambda x: x.get("score", 0),
        reverse=True,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_organ_resolver",
        "candidates_found": len(candidates),
        "ranked_construction_organs": ranked[:10],
    }


if __name__ == "__main__":
    print(json.dumps(resolve(), indent=2))
