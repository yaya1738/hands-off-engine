#!/usr/bin/env python3
"""Self-Improvement Engine — generate and durably dispatch bounded improvements.

The loop is intentionally fail-closed:
observe -> deterministic candidate -> durable dedup -> max one dispatch -> local
Task Worker result/continuation -> Factory intake -> next bounded decision.

Only existing read-only task actions are dispatched. This module never executes
arbitrary commands or modifies source code directly.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
IMPROVEMENT_STATE = STATE / "improvement_state.json"
DISPATCH_STATE = STATE / "improvement_dispatch_state.json"
DISPATCH_LOCK = STATE / "improvement_dispatch.lock"
FEEDBACK_FILE = STATE / "improvement_feedback.json"

# These actions exist in the local governed Task Worker and are deliberately read-only.
ACTION_BY_CATEGORY = {
    "reliability": ("read_file_fact", "state/health_log.jsonl"),
    "quality": ("read_file_fact", "state/learning_state.json"),
    "maintenance": ("read_file_fact", "ai/coordination/messages.jsonl"),
    "usability": ("read_file_fact", "scripts/termux_supervisor.py"),
    "security": ("read_file_fact", "scripts/comm_hub.py"),
    "expansion": ("system_status", ""),
}


def load_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}


def get_health_trend():
    log = STATE / "health_log.jsonl"
    if not log.exists():
        return {"checks": 0, "issues": 0}
    lines = log.read_text().splitlines()[-20:]
    checks = 0
    issues = 0
    for line in lines:
        try:
            entry = json.loads(line)
            checks += 1
            if not entry.get("healthy", True):
                issues += 1
        except Exception:
            continue
    return {"checks": checks, "issues": issues}


def get_learning_state():
    return load_json(STATE / "learning_state.json")


def candidate_id(category, title, description):
    raw = "\n".join((category, title, description))
    return "imp-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


# Category → safe action mapping for the improvement applier
ACTION_MAP = {
    "reliability": "log_analysis",
    "quality": "add_test",
    "maintenance": "log_analysis",
    "usability": "fix_config",
    "security": "log_analysis",
    "expansion": "generate_report",
    "documentation": "update_documentation",
}


def _candidate(category, title, description, priority):
    return {
        "id": candidate_id(category, title, description),
        "category": category,
        "title": title,
        "description": description,
        "priority": priority,
        "actionable": True,
        "action": ACTION_MAP.get(category, "update_documentation"),
    }


def get_applied_titles():
    """Load titles of already-applied improvements to avoid regeneration."""
    path = STATE / "improvement_applier_state.json"
    data = load_json(path)
    applied = data.get("applied", [])
    return {a.get("title", "") for a in applied}


def get_feedback_recommendations():
    """Load feedback recommendations to inform candidate generation."""
    if FEEDBACK_FILE.exists():
        try:
            data = json.loads(FEEDBACK_FILE.read_text())
            return data.get("summary", {}).get("category_summary", {})
        except Exception:
            pass
    return {}


def generate_improvements():
    """Generate deterministic improvement candidates from current state.

    Uses feedback data to prefer categories that historically helped
    and deprioritize categories that didn't. Skips already-applied improvements.
    """
    improvements = []
    applied = get_applied_titles()
    learning = get_learning_state()
    health = get_health_trend()
    patterns = learning.get("patterns", {})
    feedback_cats = get_feedback_recommendations()

    if health["issues"] > 0 and "Investigate health failures" not in applied:
        priority = "high"
        if feedback_cats.get("reliability", {}).get("recommendation") == "prefer":
            priority = "critical"
        improvements.append(_candidate(
            "reliability", "Investigate health failures",
            f"{health['issues']} health issues in last {health['checks']} checks. Review health_log.jsonl for patterns.",
            priority))

    # Test coverage: add tests for untested modules (skip if recently applied)
    scripts_dir = ROOT / "scripts"
    tests_dir = ROOT / "tests"
    already_added_tests = any("Add tests for" in t for t in applied)
    if scripts_dir.exists() and tests_dir.exists() and not already_added_tests:
        existing_tests = {f.stem.replace("test_", "") for f in tests_dir.glob("test_*.py")}
        untested = [f.stem for f in scripts_dir.glob("*.py")
                    if f.stem not in existing_tests and not f.stem.startswith("_")]
        if untested:
            improvements.append(_candidate(
                "quality", f"Add tests for {len(untested)} untested modules",
                f"{len(untested)} modules lack test coverage (e.g., {untested[0]}). Generate basic test stubs.",
                "medium"))

    rate = patterns.get("success_rate", 1.0)
    if rate < 0.8 and patterns.get("total_tasks", 0) > 0:
        improvements.append(_candidate(
            "quality", "Improve task validation",
            f"Success rate {rate:.0%}. Add input validation, retry logic, and error categorization.",
            "high"))

    if BUS.exists():
        lines = len(BUS.read_text().splitlines())
        if lines > 200:
            improvements.append(_candidate(
                "maintenance", "Analyze coordination bus growth",
                f"Bus has {lines} lines. Generate a read-only message-type summary; do not prune canonical messages automatically.",
                "medium"))

    if "Add Termux boot launcher" not in applied:
        improvements.append(_candidate(
            "usability", "Add Termux boot launcher",
            "Create Termux:Boot script to auto-start Node 1 + Telegram bridge + Control Room on device boot.",
            "medium"))

    if "Validate sender_id against registered parties" not in applied:
        improvements.append(_candidate(
            "security", "Validate sender_id against registered parties",
            "CommHub.receive() should reject unknown sender_ids to prevent bus poisoning.",
            "medium"))

    if patterns.get("total_tasks", 0) > 10 and rate > 0.9:
        improvements.append(_candidate(
            "expansion", "Expand autonomous task scope",
            f"System is stable ({rate:.0%} over {patterns['total_tasks']} tasks). Consider enabling autonomous web research, file analysis, or monitoring tasks.",
            "low"))

    # Feedback-driven: prefer categories that historically helped
    for cat, info in feedback_cats.items():
        if info.get("recommendation") == "prefer" and info.get("count", 0) >= 2:
            improvements.append(_candidate(
                cat, f"Continue {cat} improvements (historically effective)",
                f"Average score {info['avg_score']:.2f} over {info['count']} improvements. This category consistently helps.",
                "medium"))

    return improvements


def save_improvements(improvements):
    state = {
        "improvements": improvements,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(improvements),
    }
    IMPROVEMENT_STATE.parent.mkdir(parents=True, exist_ok=True)
    IMPROVEMENT_STATE.write_text(json.dumps(state, indent=2) + "\n")
    return state


def _load_dispatch_state():
    state = load_json(DISPATCH_STATE)
    if not isinstance(state, dict):
        state = {}
    dispatched = state.get("dispatched", {})
    pending = state.get("pending", {})    history = state.get("history", [])
    return {
        "dispatched": dispatched if isinstance(dispatched, dict) else {},
        "pending": pending if isinstance(pending, dict) else {},
        "history": history if isinstance(history, list) else [],
    }


def _save_dispatch_state(state):
    """Atomically persist the dispatch outbox and deduplication ledger."""
    DISPATCH_STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DISPATCH_STATE.with_suffix(DISPATCH_STATE.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(DISPATCH_STATE)


def _bus_contains(msg_id):
    if not BUS.exists():
        return False
    with BUS.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                if json.loads(line).get("msg_id") == msg_id:
                    return True
            except (ValueError, AttributeError):
                continue
    return False


def _append_bus(message):
    """Append once by msg_id and flush to durable storage before returning."""
    BUS.parent.mkdir(parents=True, exist_ok=True)
    if _bus_contains(message["msg_id"]):
        return False
    with BUS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def _finalize_pending(state, candidate_id_value):
    record = state["pending"].pop(candidate_id_value)
    dispatched = {
        "msg_id": record["msg_id"],
        "task_id": record["task_id"],
        "action": record["action"],
        "dispatched_at": record["dispatched_at"],
    }
    state["dispatched"][candidate_id_value] = dispatched
    state["history"].append(dispatched | {"candidate_id": candidate_id_value})
    _save_dispatch_state(state)
    return record["message"]


def _dispatch_one_locked(improvements):
    state = _load_dispatch_state()

    # Recover the one outstanding outbox item before considering new work.
    # _append_bus is idempotent, covering a crash after append but before finalize.
    if state["pending"]:
        candidate_id_value = next(iter(state["pending"]))
        record = state["pending"][candidate_id_value]
        _append_bus(record["message"])
        return _finalize_pending(state, candidate_id_value)

    now = datetime.now(timezone.utc).isoformat()
    for imp in improvements:
        cid = imp.get("id")
        if not isinstance(cid, str) or not cid or cid in state["dispatched"]:
            continue
        action, target = ACTION_BY_CATEGORY.get(imp.get("category"), (None, None))
        if action is None:
            continue

        msg_id = "imp-task-" + hashlib.sha256(cid.encode("utf-8")).hexdigest()[:20]
        task_id = "task-" + cid
        message = {
            "msg_id": msg_id,
            "timestamp": now,
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "context": {
                "task_id": task_id,
                "action": action,
                "params": {"file_path": target} if target else {},
                "reply_to": "self_improvement",
                "correlation_id": cid,
            },
            "payload": {
                "candidate_id": cid,
                "category": imp["category"],
                "title": imp.get("title", ""),
                "description": imp.get("description", ""),
            },
        }

        # Write an outbox record first. On restart, pending work is replayed
        # idempotently and then promoted to dispatched; no task is silently lost.
        state["pending"][cid] = {
            "msg_id": msg_id,
            "task_id": task_id,
            "action": action,
            "dispatched_at": now,
            "message": message,
        }
        _save_dispatch_state(state)
        _append_bus(message)
        return _finalize_pending(state, cid)

    _save_dispatch_state(state)
    return None


def dispatch_one(improvements):
    """Serialize dispatch and recover at most one durable outbox task."""
    STATE.mkdir(parents=True, exist_ok=True)
    with DISPATCH_LOCK.open("a", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            return _dispatch_one_locked(improvements)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

def run():
    improvements = generate_improvements()
    state = save_improvements(improvements)
    dispatched = dispatch_one(improvements)
    state["dispatched"] = dispatched

    print(f"Self-improvement: {len(improvements)} improvements generated")
    if dispatched:
        print(f"  dispatched: {dispatched['task_id']} -> {dispatched['action']}")
    else:
        print("  dispatched: none (all candidates already handled or unsupported)")
    for imp in improvements:
        print(f"  [{imp['priority']}] {imp['category']}: {imp['title']}")

    return state


if __name__ == "__main__":
    run()