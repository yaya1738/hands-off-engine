import ast
import json
from datetime import datetime, timezone
from pathlib import Path


FILES = [
    "ai/factory/runtime.py",
    "ai/factory/development_tracker.py",
    "ai/factory/development_translator.py",
    "ai/factory/development_advisor.py",
    "ai/factory/improvement_planner.py",
    "ai/factory/improvement_approval.py",
    "ai/factory/improvement_executor.py",
]


KEYWORDS = [
    "verify_task",
    "verified",
    "translate",
    "analyze",
    "plan",
    "proposal",
    "request",
    "approve",
    "execute",
]


def scan_file(path):
    result = {
        "file": path,
        "methods": [],
        "matches": []
    }

    try:
        source = Path(path).read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result["methods"].append({
                    "name": node.name,
                    "line": node.lineno
                })

        for i, line in enumerate(source.splitlines(), 1):
            for keyword in KEYWORDS:
                if keyword.lower() in line.lower():
                    result["matches"].append({
                        "line": i,
                        "keyword": keyword,
                        "text": line.strip()
                    })

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit": "factory proposal bridge truth audit",
        "target_flow": [
            "verified task",
            "proposal generation",
            "approval boundary",
            "FactoryImprovementExecutor.execute"
        ],
        "files": []
    }

    for file in FILES:
        report["files"].append(scan_file(file))

    analysis = {
        "verified_task_locations": [],
        "proposal_candidates": [],
        "approval_candidates": [],
        "executor_locations": []
    }

    for item in report["files"]:
        for match in item.get("matches", []):
            text = match["text"].lower()

            if "verify" in text or "verified" in text:
                analysis["verified_task_locations"].append(
                    {
                        "file": item["file"],
                        "line": match["line"],
                        "text": match["text"]
                    }
                )

            if "proposal" in text or "translate" in text or "plan" in text:
                analysis["proposal_candidates"].append(
                    {
                        "file": item["file"],
                        "line": match["line"],
                        "text": match["text"]
                    }
                )

            if "approval" in text or "approve" in text:
                analysis["approval_candidates"].append(
                    {
                        "file": item["file"],
                        "line": match["line"],
                        "text": match["text"]
                    }
                )

            if "execute" in text:
                analysis["executor_locations"].append(
                    {
                        "file": item["file"],
                        "line": match["line"],
                        "text": match["text"]
                    }
                )

    report["analysis"] = analysis

    with open("factory_proposal_bridge_truth_audit.json", "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({
        "status": "complete",
        "output": "factory_proposal_bridge_truth_audit.json",
        "files_scanned": len(FILES),
        "verified_hits": len(analysis["verified_task_locations"]),
        "proposal_hits": len(analysis["proposal_candidates"]),
        "approval_hits": len(analysis["approval_candidates"]),
        "executor_hits": len(analysis["executor_locations"])
    }, indent=2))


if __name__ == "__main__":
    main()
