#!/usr/bin/env python3
"""Read-only meta-metrics; repository operations belong to FactoryAuthorityGateway."""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_git_root():
    """Return the known repository root without spawning git."""
    return ROOT


def get_recent_commits(days=30):
    """Commit history requires authority; return an explicit non-executing result."""
    return []


def classify_commit(message):
    text = message.lower()
    if any(k in text for k in ("enforce", "hook", "ci", "check", "lint", "validate")):
        return "enforcement"
    if any(k in text for k in ("fix", "harden", "security", "safe", "protect", "guard")):
        return "hardening"
    if any(k in text for k in ("doc", "readme", "comment", "explain")):
        return "docs"
    if any(k in text for k in ("feat", "add", "implement", "new", "create", "build")):
        return "feature"
    return "other"


def analyze_work_distribution(days=30):
    distribution = defaultdict(int)
    commits = get_recent_commits(days)
    for commit in commits:
        parts = commit.split(" ", 1)
        if len(parts) > 1:
            distribution[classify_commit(parts[1])] += 1
    total = sum(distribution.values())
    return {"counts": dict(distribution), "percentages": {k: v / total * 100 for k, v in distribution.items()} if total else {}, "total_commits": total, "period_days": days, "history_source": "FactoryAuthorityGateway required"}


def check_enforcement_coverage(root):
    standards = root / "docs" / "DEVELOPMENT_STANDARDS.md"
    if not standards.exists():
        return {"error": "DEVELOPMENT_STANDARDS.md not found"}
    content = standards.read_text()
    rules = re.findall(r"- \[[ x]\].*(?:must|should|always|never)", content, re.IGNORECASE)
    enforcement_files = list((root / "scripts").glob("*hook*")) + list((root / "scripts").glob("*check*")) + list((root / ".github" / "workflows").glob("*.yml"))
    return {"documented_rules": len(rules), "enforcement_files": len(enforcement_files), "enforcement_file_list": [str(f.relative_to(root)) for f in enforcement_files], "coverage_estimate": "manual review needed"}


def check_doc_coverage(root):
    py_files = [f for f in root.glob("**/*.py") if ".git" not in f.parts and "__pycache__" not in f.parts]
    doc_files = []
    for part in ("docs", ".claude", ".github", "ai"):
        doc_files.extend((root / part).glob("**/*.md"))
    knowledge = root / "state" / "knowledge.json"
    registered = []
    ephemeral = []
    if knowledge.exists():
        try:
            data = json.loads(knowledge.read_text())
            registered = data.get("required_reading", []) + data.get("optional_docs", []) + data.get("agent_instruction_files", [])
            ephemeral = [k for e in data.get("ephemeral_docs_excluded", []) for k in ("SESSION", "SUMMARY", "LOG") if k in e.upper()]
        except (OSError, ValueError, TypeError):
            pass
    unregistered = sum(1 for f in doc_files if str(f.relative_to(root)) not in registered and not any(k in str(f).upper() for k in ephemeral))
    return {"python_files": len(py_files), "markdown_files": len(doc_files), "registered_in_knowledge_json": len(registered), "unregistered_docs": unregistered}


def check_meta_debt_indicators(root):
    indicators = {"todo_comments": 0, "fixme_comments": 0, "deferred_work_mentions": 0}
    for path in root.glob("**/*"):
        if not path.is_file() or ".git" in path.parts or path.suffix not in {".py", ".md"}:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        indicators["todo_comments"] += sum(1 for line in text.splitlines() if "TODO" in line)
        indicators["fixme_comments"] += sum(1 for line in text.splitlines() if "FIXME" in line)
        indicators["deferred_work_mentions"] += sum(1 for line in text.splitlines() if "later" in line.lower())
    return indicators


def generate_report():
    root = get_git_root()
    return {"generated_at": datetime.now().isoformat(), "work_distribution": analyze_work_distribution(), "enforcement_coverage": check_enforcement_coverage(root), "doc_coverage": check_doc_coverage(root), "meta_debt_indicators": check_meta_debt_indicators(root)}


def print_report(report):
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    print_report(generate_report())
