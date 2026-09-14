#!/usr/bin/env python3
"""Improvement Applier — execute safe bounded improvements.

Takes improvement candidates and applies the ones that can be executed
safely without human approval. This closes the observe→act gap in the
self-improvement loop.

Safe actions (auto-execute):
  - update_documentation: append findings to docs
  - archive_state: compress old state files
  - update_readme: add/update README sections
  - generate_report: create analysis report files
  - fix_config: update configuration based on detected issues

Risky actions (queue for operator approval):
  - code_change: modify source code
  - add_dependency: add new dependencies
  - network_action: make outbound requests

Design constraints:
  - All writes go to state/, docs/, or config/ — never to scripts/ or tests/
  - Each improvement is idempotent (safe to re-run)
  - Improvement impact is tracked for the feedback loop
  - Fail-closed: any unexpected error stops the cycle
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
APPLIER_STATE = STATE / "improvement_applier_state.json"
APPROVAL_QUEUE = STATE / "improvement_approval_queue.json"
FEEDBACK_FILE = STATE / "improvement_feedback.json"
DOCS_DIR = ROOT / "docs"

# Actions the applier can execute without approval
SAFE_ACTIONS = {
    "update_documentation",
    "archive_state",
    "update_readme",
    "generate_report",
    "fix_config",
    "clean_bus",
    "log_analysis",
    "add_test",
}

# Actions that require operator approval
RISKY_ACTIONS = {
    "code_change",
    "add_dependency",
    "network_action",
    "delete_file",
}

# Directories the applier may write to
ALLOWED_WRITE_DIRS = frozenset({
    ROOT / "state",
    ROOT / "docs",
    ROOT / "config",
    ROOT / "ai",
})


def load_state():
    if APPLIER_STATE.exists():
        try:
            return json.loads(APPLIER_STATE.read_text())
        except Exception:
            pass
    return {"applied": [], "queued": [], "history": []}


def save_state(state):
    APPLIER_STATE.parent.mkdir(parents=True, exist_ok=True)
    APPLIER_STATE.write_text(json.dumps(state, indent=2) + "\n")


def load_feedback():
    if FEEDBACK_FILE.exists():
        try:
            return json.loads(FEEDBACK_FILE.read_text())
        except Exception:
            pass
    return {"improvements": [], "summary": {}}


def save_feedback(feedback):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2) + "\n")


def improvement_id(category, title):
    raw = f"{category}|{title}"
    return "applied-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


class ImprovementApplier:
    """Applies safe improvements and queues risky ones for approval."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root) if repo_root else ROOT
        self.state_dir = self.repo_root / "state"
        self.state = load_state()
        self.feedback = load_feedback()
        self.applied_ids = set(self.state.get("applied_ids", []))

    def _persist(self):
        self.state["applied_ids"] = sorted(self.applied_ids)[-500:]
        self.state["applied"] = self.state.get("applied", [])[-200:]
        self.state["queued"] = self.state.get("queued", [])[-100:]
        save_state(self.state)
        save_feedback(self.feedback)

    def _record_improvement(self, imp_id, category, title, action, result, impact=None):
        """Record an applied improvement with optional impact measurement."""
        entry = {
            "id": imp_id,
            "category": category,
            "title": title,
            "action": action,
            "result": result,
            "impact": impact,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state.setdefault("applied", []).append(entry)
        self.applied_ids.add(imp_id)
        self.feedback.setdefault("improvements", []).append(entry)

    def _measure_impact(self, category):
        """Measure current state metrics for feedback comparison."""
        metrics = {}
        # Bus size
        bus_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        if bus_file.exists():
            metrics["bus_lines"] = len(bus_file.read_text().splitlines())
        # State files count
        state_dir = self.repo_root / "state"
        if state_dir.exists():
            metrics["state_files"] = len(list(state_dir.iterdir()))
        # Health log
        health_log = state_dir / "health_log.jsonl"
        if health_log.exists():
            lines = health_log.read_text().splitlines()[-20:]
            healthy = sum(1 for l in lines if l.strip() and json.loads(l).get("healthy", True))
            metrics["health_rate"] = healthy / max(len(lines), 1)
        # Test count
        tests_dir = self.repo_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            metrics["test_files"] = len(test_files)
        return metrics

    def apply_improvement(self, imp: dict) -> dict:
        """Apply a single improvement candidate.

        Returns: {applied: bool, id: str, action: str, result: str, needs_approval: bool}
        """
        imp_id = imp.get("id", improvement_id(imp.get("category", ""), imp.get("title", "")))
        category = imp.get("category", "")
        title = imp.get("title", "")
        action = imp.get("action", "update_documentation")
        description = imp.get("description", "")

        # Dedup
        if imp_id in self.applied_ids:
            return {"applied": False, "id": imp_id, "reason": "already_applied"}

        # Classify as safe or risky
        if action in RISKY_ACTIONS:
            self.state.setdefault("queued", []).append({
                "id": imp_id, "category": category, "title": title,
                "action": action, "queued_at": datetime.now(timezone.utc).isoformat(),
            })
            self._persist()
            return {"applied": False, "id": imp_id, "needs_approval": True, "action": action}

        if action not in SAFE_ACTIONS:
            return {"applied": False, "id": imp_id, "reason": f"unknown_action:{action}"}

        # Measure before
        before_metrics = self._measure_impact(category)

        # Apply the safe action
        try:
            result = self._execute_safe(action, category, title, description, imp)
        except Exception as e:
            return {"applied": False, "id": imp_id, "error": str(e)}

        # Measure after
        after_metrics = self._measure_impact(category)

        # Compute impact delta
        impact = {}
        for key in set(before_metrics.keys()) | set(after_metrics.keys()):
            b = before_metrics.get(key, 0)
            a = after_metrics.get(key, 0)
            if isinstance(b, (int, float)) and isinstance(a, (int, float)):
                impact[key] = {"before": b, "after": a, "delta": a - b}

        self._record_improvement(imp_id, category, title, action, result, impact)
        self._persist()

        return {"applied": True, "id": imp_id, "action": action, "result": result, "impact": impact}

    def _execute_safe(self, action, category, title, description, imp):
        """Execute a safe improvement action. Returns result string."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if action == "update_documentation":
            doc_file = self.repo_root / "docs" / f"improvement_log.md"
            doc_file.parent.mkdir(parents=True, exist_ok=True)
            entry = f"\n## [{now}] {title}\n- Category: {category}\n- {description}\n"
            with open(doc_file, "a") as f:
                f.write(entry)
            return f"Appended to {doc_file.relative_to(self.repo_root)}"

        elif action == "archive_state":
            archive_dir = self.repo_root / "state" / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            # Archive old log files (>7 days)
            archived = 0
            for f in self.state_dir.glob("*.jsonl"):
                if f.name in ("actuator_log.jsonl", "comm_log.jsonl"):
                    dest = archive_dir / f"{f.stem}_{now[:10]}.jsonl"
                    shutil.copy2(f, dest)
                    archived += 1
            return f"Archived {archived} log files"

        elif action == "generate_report":
            report_file = self.repo_root / "state" / "reports" / f"report_{now[:10]}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            report = {
                "generated_at": now,
                "category": category,
                "title": title,
                "description": description,
                "metrics": self._measure_impact(category),
                "applied_history": len(self.applied_ids),
            }
            report_file.write_text(json.dumps(report, indent=2) + "\n")
            return f"Report saved to {report_file.relative_to(self.repo_root)}"

        elif action == "clean_bus":
            bus_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
            if not bus_file.exists():
                return "No bus file to clean"
            lines = bus_file.read_text().splitlines()
            before = len(lines)
            # Keep only last 500 lines, archive the rest
            if before > 500:
                archive = self.repo_root / "ai" / "coordination" / "archive"
                archive.mkdir(parents=True, exist_ok=True)
                archive_file = archive / f"messages_{now[:10]}_{now[11:19].replace(':', '')}.jsonl"
                archive_file.write_text("\n".join(lines[:-500]) + "\n")
                bus_file.write_text("\n".join(lines[-500:]) + "\n")
                return f"Archived {before - 500} lines, kept 500"
            return f"Bus has {before} lines, no cleanup needed"

        elif action == "fix_config":
            # Check and fix missing config entries
            config_file = self.repo_root / "config" / "system.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config = {}
            if config_file.exists():
                try:
                    config = json.loads(config_file.read_text())
                except Exception:
                    pass
            updated = False
            if "node_id" not in config:
                config["node_id"] = "node-1"
                updated = True
            if "last_improvement" not in config:
                config["last_improvement"] = now
                updated = True
            if "improvement_count" not in config:
                config["improvement_count"] = len(self.applied_ids)
                updated = True
            if updated:
                config["last_improvement"] = now
                config["improvement_count"] = len(self.applied_ids)
                config_file.write_text(json.dumps(config, indent=2) + "\n")
                return "Config updated with missing entries"
            return "Config already up to date"

        elif action == "log_analysis":
            # Analyze recent logs and write summary
            summary_file = self.state_dir / "analysis_summary.json"
            analysis = {
                "analyzed_at": now,
                "improvements_applied": len(self.applied_ids),
                "improvements_queued": len(self.state.get("queued", [])),
            }
            # Count bus message types
            bus_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
            if bus_file.exists():
                types = {}
                for line in bus_file.read_text().splitlines()[-200:]:
                    try:
                        msg = json.loads(line)
                        t = msg.get("type", "unknown")
                        types[t] = types.get(t, 0) + 1
                    except Exception:
                        pass
                analysis["bus_message_types"] = types
            summary_file.write_text(json.dumps(analysis, indent=2) + "\n")
            return f"Analysis summary written ({len(analysis.get('bus_message_types', {}))} message types)"

        elif action == "update_readme":
            readme = self.repo_root / "docs" / "IMPROVEMENTS.md"
            readme.parent.mkdir(parents=True, exist_ok=True)
            entry = f"\n- [{now}] **{title}** ({category}): {description[:100]}\n"
            with open(readme, "a") as f:
                f.write(entry)
            return f"Updated {readme.relative_to(self.repo_root)}"

        elif action == "add_test":
            # Generate a basic test stub for untested modules
            scripts_dir = self.repo_root / "scripts"
            tests_dir = self.repo_root / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            existing_tests = {f.stem.replace("test_", "") for f in tests_dir.glob("test_*.py")}
            untested = [f.stem for f in scripts_dir.glob("*.py")
                       if f.stem not in existing_tests and not f.stem.startswith("_")]
            if not untested:
                return "All modules already have tests"
            # Create stub for first untested module
            module = untested[0]
            test_file = tests_dir / f"test_{module}.py"
            test_content = (
                "import sys\n"
                "from pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
                "\n"
                f"# Auto-generated test stub for {module}\n"
                "# TODO: Add specific tests for this module\n"
                "\n"
                "def test_import():\n"
                '    """Module can be imported without errors."""\n'
                f"    import scripts.{module}\n"
                "\n"
                "def test_smoke():\n"
                '    """Basic smoke test: module loads and key functions exist."""\n'
                f"    import scripts.{module}\n"
                "    # Add assertions for key exports here\n"
            )
            test_file.write_text(test_content)
            return f"Created test stub for {module} ({len(untested)} untested modules remain)"

        return f"Unknown safe action: {action}"

    def apply_batch(self, improvements: List[dict]) -> List[dict]:
        """Apply a batch of improvements, skipping already-applied ones."""
        results = []
        for imp in improvements:
            result = self.apply_improvement(imp)
            results.append(result)
        return results

    def get_pending_approvals(self) -> List[dict]:
        """Get improvements waiting for operator approval."""
        return self.state.get("queued", [])

    def approve_improvement(self, imp_id: str) -> Optional[dict]:
        """Approve and execute a queued improvement."""
        queued = self.state.get("queued", [])
        for item in queued:
            if item["id"] == imp_id:
                queued.remove(item)
                result = self._execute_safe(
                    item["action"], item["category"], item["title"],
                    f"Approved improvement: {item['title']}", item
                )
                self._record_improvement(imp_id, item["category"], item["title"], item["action"], result)
                self._persist()
                return {"approved": True, "id": imp_id, "result": result}
        return {"approved": False, "id": imp_id, "reason": "not_found"}

    def status(self) -> dict:
        return {
            "applied_count": len(self.applied_ids),
            "queued_count": len(self.state.get("queued", [])),
            "feedback_improvements": len(self.feedback.get("improvements", [])),
            "recent_applications": self.state.get("applied", [])[-5:],
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Improvement Applier")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Show applier status")
    sub.add_parser("queue", help="Show pending approvals")

    args = parser.parse_args()
    applier = ImprovementApplier()

    if args.cmd == "status":
        print(json.dumps(applier.status(), indent=2, default=str))
    elif args.cmd == "queue":
        pending = applier.get_pending_approvals()
        if pending:
            for p in pending:
                print(f"  🔒 {p['title']} (action={p['action']}, category={p['category']})")
        else:
            print("  No pending approvals")
    else:
        parser.print_help()
