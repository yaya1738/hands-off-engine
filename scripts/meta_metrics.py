#!/usr/bin/env python3
"""
Meta-Metrics: Make invisible value visible.

This script measures things that are typically invisible:
- Work type distribution (features vs hardening vs enforcement)
- Enforcement coverage (% of rules with checks)
- Documentation coverage (% of components documented)
- Meta-debt indicators

Created as fix for Layer 61 of root cause analysis.
See docs/DEVELOPMENT_STANDARDS.md for full context.
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def get_git_root():
    """Get the root of the git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True
    )
    return Path(result.stdout.strip())

def get_recent_commits(days=30):
    """Get commits from the last N days."""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = subprocess.run(
        ["git", "log", f"--since={since_date}", "--oneline", "--all"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []

def classify_commit(message):
    """Classify a commit as feature, hardening, enforcement, docs, or other."""
    message_lower = message.lower()

    # Hardening keywords
    hardening_keywords = [
        "fix", "harden", "enforce", "monitor", "check", "validate",
        "security", "safe", "protect", "guard", "defensive"
    ]

    # Feature keywords
    feature_keywords = [
        "feat", "add", "implement", "new", "create", "build"
    ]

    # Enforcement keywords
    enforcement_keywords = [
        "enforce", "hook", "pre-commit", "ci", "check", "lint", "validate"
    ]

    # Docs keywords
    docs_keywords = [
        "doc", "readme", "comment", "explain", "describe"
    ]

    if any(kw in message_lower for kw in enforcement_keywords):
        return "enforcement"
    elif any(kw in message_lower for kw in hardening_keywords):
        return "hardening"
    elif any(kw in message_lower for kw in docs_keywords):
        return "docs"
    elif any(kw in message_lower for kw in feature_keywords):
        return "feature"
    else:
        return "other"

def analyze_work_distribution(days=30):
    """Analyze distribution of work types in recent commits."""
    commits = get_recent_commits(days)
    distribution = defaultdict(int)

    for commit in commits:
        if commit:
            # Skip the hash, get the message
            parts = commit.split(" ", 1)
            if len(parts) > 1:
                message = parts[1]
                work_type = classify_commit(message)
                distribution[work_type] += 1

    total = sum(distribution.values())
    percentages = {k: (v/total*100 if total > 0 else 0) for k, v in distribution.items()}

    return {
        "counts": dict(distribution),
        "percentages": percentages,
        "total_commits": total,
        "period_days": days
    }

def check_enforcement_coverage(root):
    """Check what percentage of documented rules have enforcement."""
    # Look for rules in DEVELOPMENT_STANDARDS.md
    standards_file = root / "docs" / "DEVELOPMENT_STANDARDS.md"
    if not standards_file.exists():
        return {"error": "DEVELOPMENT_STANDARDS.md not found"}

    content = standards_file.read_text()

    # Count rules (lines with "must", "should", "always", "never" in checklists)
    rule_patterns = [
        r"- \[ \].*(?:must|should|always|never)",
        r"- \[x\].*(?:must|should|always|never)",
    ]

    rules = []
    for pattern in rule_patterns:
        rules.extend(re.findall(pattern, content, re.IGNORECASE))

    # Check for enforcement mechanisms
    enforcement_files = list((root / "scripts").glob("*hook*")) + \
                       list((root / "scripts").glob("*check*")) + \
                       list((root / ".github" / "workflows").glob("*.yml"))

    return {
        "documented_rules": len(rules),
        "enforcement_files": len(enforcement_files),
        "enforcement_file_list": [str(f.relative_to(root)) for f in enforcement_files],
        "coverage_estimate": "manual review needed"
    }

def check_doc_coverage(root):
    """Check documentation coverage."""
    # Count Python files
    py_files = list(root.glob("**/*.py"))
    py_files = [f for f in py_files if ".git" not in str(f) and "__pycache__" not in str(f)]

    # Count doc files
    doc_files = list(root.glob("docs/**/*.md")) + list(root.glob("**/*.md"))
    doc_files = [f for f in doc_files if ".git" not in str(f)]

    # Check knowledge.json
    knowledge_file = root / "state" / "knowledge.json"
    registered_docs = 0
    if knowledge_file.exists():
        try:
            knowledge = json.loads(knowledge_file.read_text())
            required = knowledge.get("required_reading", [])
            optional = knowledge.get("optional_docs", [])
            registered_docs = len(required) + len(optional)
        except:
            pass

    return {
        "python_files": len(py_files),
        "markdown_files": len(doc_files),
        "registered_in_knowledge_json": registered_docs,
        "unregistered_docs": len(doc_files) - registered_docs if registered_docs > 0 else "unknown"
    }

def check_meta_debt_indicators(root):
    """Check for indicators of meta-debt."""
    indicators = {}

    # Check for TODO comments
    result = subprocess.run(
        ["grep", "-r", "TODO", "--include=*.py", str(root)],
        capture_output=True, text=True
    )
    indicators["todo_comments"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    # Check for FIXME comments
    result = subprocess.run(
        ["grep", "-r", "FIXME", "--include=*.py", str(root)],
        capture_output=True, text=True
    )
    indicators["fixme_comments"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    # Check for "later" in comments (deferred work)
    result = subprocess.run(
        ["grep", "-ri", "later", "--include=*.py", "--include=*.md", str(root)],
        capture_output=True, text=True
    )
    indicators["deferred_work_mentions"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

    return indicators

def generate_report():
    """Generate full meta-metrics report."""
    root = get_git_root()

    report = {
        "generated_at": datetime.now().isoformat(),
        "work_distribution": analyze_work_distribution(30),
        "enforcement_coverage": check_enforcement_coverage(root),
        "doc_coverage": check_doc_coverage(root),
        "meta_debt_indicators": check_meta_debt_indicators(root)
    }

    return report

def print_report(report):
    """Print human-readable report."""
    print("=" * 60)
    print("META-METRICS REPORT")
    print("Making invisible value visible")
    print("=" * 60)
    print(f"\nGenerated: {report['generated_at']}")

    print("\n## WORK DISTRIBUTION (last 30 days)")
    print("-" * 40)
    wd = report["work_distribution"]
    print(f"Total commits: {wd['total_commits']}")
    for work_type, pct in sorted(wd["percentages"].items(), key=lambda x: -x[1]):
        count = wd["counts"].get(work_type, 0)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {work_type:12} {bar} {pct:5.1f}% ({count})")

    # Flag if hardening is too low
    hardening_pct = wd["percentages"].get("hardening", 0) + wd["percentages"].get("enforcement", 0)
    if hardening_pct < 20:
        print(f"\n  ⚠️  WARNING: Hardening+Enforcement is only {hardening_pct:.1f}%")
        print("     Recommendation: Balance feature work with hardening")

    print("\n## ENFORCEMENT COVERAGE")
    print("-" * 40)
    ec = report["enforcement_coverage"]
    print(f"Documented rules: {ec.get('documented_rules', 'unknown')}")
    print(f"Enforcement files: {ec.get('enforcement_files', 0)}")
    for f in ec.get("enforcement_file_list", [])[:5]:
        print(f"  - {f}")

    print("\n## DOCUMENTATION COVERAGE")
    print("-" * 40)
    dc = report["doc_coverage"]
    print(f"Python files: {dc['python_files']}")
    print(f"Markdown files: {dc['markdown_files']}")
    print(f"Registered in knowledge.json: {dc['registered_in_knowledge_json']}")
    if isinstance(dc["unregistered_docs"], int) and dc["unregistered_docs"] > 0:
        print(f"  ⚠️  WARNING: {dc['unregistered_docs']} docs not registered")

    print("\n## META-DEBT INDICATORS")
    print("-" * 40)
    md = report["meta_debt_indicators"]
    print(f"TODO comments: {md['todo_comments']}")
    print(f"FIXME comments: {md['fixme_comments']}")
    print(f"'Later' mentions: {md['deferred_work_mentions']}")

    if md["deferred_work_mentions"] > 10:
        print(f"\n  ⚠️  WARNING: High deferred work ({md['deferred_work_mentions']} mentions)")
        print("     Remember: 'Later' means 'never' in autonomous systems")

    print("\n" + "=" * 60)
    print("See docs/DEVELOPMENT_STANDARDS.md for context on these metrics")
    print("=" * 60)

if __name__ == "__main__":
    import sys

    report = generate_report()

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
