import os
import json
import ast
from datetime import datetime

ROOT = "ai/factory"

TARGETS = [
    "runtime.py",
    "development_tracker.py",
    "development_translator.py",
    "development_advisor.py",
    "improvement_planner.py",
    "improvement_approval.py",
    "improvement_executor.py",
]

KEYWORDS = [
    "verified",
    "proposal",
    "plan",
    "approval",
    "approve",
    "execute",
    "executor",
    "create_task",
    "verify_task",
    "handoff",
]


def scan_file(path):
    result = {
        "file": path,
        "methods": [],
        "matches": []
    }

    try:
        with open(path, "r") as f:
            source = f.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["methods"].append({
                    "name": node.name,
                    "line": node.lineno
                })

        for i, line in enumerate(source.splitlines(), 1):
            lower = line.lower()
            for keyword in KEYWORDS:
                if keyword in lower:
                    result["matches"].append({
                        "line": i,
                        "keyword": keyword,
                        "text": line.strip()
                    })

    except Exception as e:
        result["error"] = str(e)

    return result


def find_history():
    found = []

    for root, dirs, files in os.walk("."):
        for file in files:
            name = file.lower()

            if any(x in name for x in [
                "audit",
                "handoff",
                "history",
                "report",
                "provenance"
            ]):
                found.append(os.path.join(root, file))

    return found


audit = {
    "timestamp": datetime.utcnow().isoformat(),
    "purpose": "factory lifecycle truth audit",
    "target_flow": [
        "verified development task",
        "proposal representation",
        "approval boundary",
        "FactoryImprovementExecutor.execute"
    ],
    "files": [],
    "historical_artifacts": find_history(),
}


for target in TARGETS:
    path = os.path.join(ROOT, target)
    if os.path.exists(path):
        audit["files"].append(scan_file(path))


with open("factory_lifecycle_truth_audit.json", "w") as f:
    json.dump(audit, f, indent=2, default=str)


print(json.dumps({
    "status": "complete",
    "output": "factory_lifecycle_truth_audit.json",
    "files_scanned": len(audit["files"]),
    "historical_artifacts_found": len(audit["historical_artifacts"])
}, indent=2))
