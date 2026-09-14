#!/usr/bin/env python3
"""Self-Improvement Engine — generate and durably dispatch bounded improvements.

The loop is intentionally fail-closed:
observe -> deterministic candidate -> durable dedup -> max one dispatch -> AnyClaw
result/continuation -> Factory intake -> next bounded decision.

Only existing read-only task actions are dispatched. This module never executes
arbitrary commands or modifies source code directly.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
IMPROVEMENT_STATE = STATE / "improvement_state.json"
DISPATCH_STATE = STATE / "improvement_dispatch_state.json"
FEEDBACK_FILE = STATE / "improvement_feedback.json"

# These actions already exist in the AnyClaw worker and are deliberately read-only.
ACTION_BY_CATEGORY = {
    "reliability": ("read_file_fact", "state/health_log.jsonl"),
    "quality": ("read_file_fact", "state/learning_state.json"),
    "maintenance": ("read_file_fact", "ai/coordination/messages.jsonl"),
    "usability": ("read_file_fact", ".termux/boot/hands-off-engine.sh"),
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
    "quality": "generate_report",
    "maintenance": "clean_bus",
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
    and deprioritize categories that didn't.
    """
    improvements = []
    learning = get_learning_state()
    health = get_health_trend()
    patterns = learning.get("patterns", {})
    feedback_cats = get_feedback_recommendations()

    if health["issues"] > 0:
        priority = "high"
        if feedback_cats.get("reliability", {}).get("recommendation") == "prefer":
            priority = "critical"
        improvements.append(_candidate(
            "reliability", "Investigate health failures",
            f"{health['issues']} health issues in last {health['checks']} checks. Review health_log.jsonl for patterns.",
            priority))

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
                "maintenance", "Clean up bus messages",
                f"Bus has {lines} lines. Archive old continuation events, keep task_assignments and results.",
                "medium"))

    improvements.append(_candidate(
        "usability", "Add Termux boot launcher",
        "Create Termux:Boot script to auto-start Node 1 + Telegram bridge + Control Room on device boot.",
        "medium"))

    improvements.append(_candidate(
        "security", "Validate sender_id against registered parties",
        "CommHub.receive() should reject unknown sender_ids to prevent bus poisoning.",
        "medium"))

    if patterns.get("total_tasks", 0) > 10 and rate > 0.9:
        improvements.append(_candidate(
            "expansion", "Expand autonomous task scope",
            f"System is stable ({rate:.0%} over {patterns['total_tasks']} tasks). Consider enabling autonomous web research, file analysis, or monitoring tasks.",
            "low"))

    # Feedback-driven: add improvement applier cycle if not yet running
    applier_state = STATE / "improvement_applier_state.json"
    if not applier_state.exists() or json.loads(applier_state.read_text() if applier_state.exists() else "{}").get("applied_ids", []) == []:
        improvements.append(_candidate(
            "maintenance", "Initialize improvement applier",
            "Run the improvement applier to start the observe→act→measure loop.",
            "high"))

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
    return {
        "dispatched": state.get("dispatched", {}),
        "history": state.get("history", []),
    }


def _append_bus(message):
    BUS.parent.mkdir(parents=True, exist_ok=True)
    with BUS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, sort_keys=True) + "\n")


def dispatch_one(improvements):
    """Dispatch at most one new bounded candidate and persist the decision first."""
    state = _load_dispatch_state()
    now = datetime.now(timezone.utc).isoformat()

    for imp in improvements:
        cid = imp["id"]
        if cid in state["dispatched"]:
            continue
        action, target = ACTION_BY_CATEGORY.get(imp["category"], (None, None))
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
            "task_id": task_id,
            "action": action,
            "params": {"path": target} if target else {},
            "payload": {
                "candidate_id": cid,
                "category": imp["category"],
                "title": imp["title"],
                "description": imp["description"],
            },
            "reply_to": "self_improvement",
        }

        # Record the durable decision before the bus write. If the process dies
        # after this point, the candidate remains closed rather than duplicating work.
        state["dispatched"][cid] = {
            "msg_id": msg_id,
            "task_id": task_id,
            "action": action,
            "dispatched_at": now,
        }
        state["history"].append(state["dispatched"][cid] | {"candidate_id": cid})
        DISPATCH_STATE.parent.mkdir(parents=True, exist_ok=True)
        DISPATCH_STATE.write_text(json.dumps(state, indent=2) + "\n")
        _append_bus(message)
        return message

    DISPATCH_STATE.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_STATE.write_text(json.dumps(state, indent=2) + "\n")
    return None


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
