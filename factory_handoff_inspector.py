import ast
import json
from pathlib import Path
from datetime import datetime


FILES = [
    "ai/factory/runtime.py",
    "ai/factory/development_tracker.py",
    "ai/factory/development_translator.py",
    "ai/factory/development_advisor.py",
    "ai/factory/improvement_planner.py",
    "ai/factory/improvement_approval.py",
    "ai/factory/improvement_executor.py",
]


def extract_methods(path):
    results = []
    try:
        source = Path(path).read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                results.append({
                    "name": node.name,
                    "line": node.lineno,
                    "file": path
                })
            elif isinstance(node, ast.ClassDef):
                results.append({
                    "class": node.name,
                    "line": node.lineno,
                    "file": path
                })

    except Exception as e:
        results.append({
            "file": path,
            "error": str(e)
        })

    return results


def search_keywords(path, keywords):
    hits = []
    try:
        lines = Path(path).read_text().splitlines()

        for i, line in enumerate(lines, 1):
            for word in keywords:
                if word in line:
                    hits.append({
                        "file": path,
                        "line": i,
                        "keyword": word,
                        "text": line.strip()
                    })

    except Exception:
        pass

    return hits


report = {
    "timestamp": datetime.utcnow().isoformat(),
    "inspection": "factory proposal handoff audit",
    "files": FILES,
    "methods": [],
    "keywords": [],
    "analysis": {}
}


for f in FILES:
    report["methods"].extend(extract_methods(f))
    report["keywords"].extend(
        search_keywords(
            f,
            [
                "verified",
                "proposal",
                "plan",
                "translate",
                "execute",
                "approval",
                "task",
                "handoff"
            ]
        )
    )


report["analysis"] = {
    "question_1": "Where does verified task creation exist?",
    "question_2": "Where does proposal generation exist?",
    "question_3": "What lifecycle bridge is missing?",
    "next_step": "Review runtime transition and insert minimal adapter only if absent."
}


print(json.dumps(report, indent=2, default=str))
