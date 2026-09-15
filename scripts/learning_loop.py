#!/usr/bin/env python3
"""Learning Loop — records task outcomes and suggests improvements.

Reads completion events from messages.jsonl, tracks success/failure rates,
and emits improvement suggestions to a learning state file. This is the
start of a self-improving system.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
STATE = ROOT / "state" / "learning_state.json"


def load_bus_events():
    """Load all messages from the bus."""
    if not BUS.exists():
        return []
    msgs = []
    for line in BUS.read_text().splitlines():
        try:
            msgs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return msgs


def load_state():
    """Load persistent learning state."""
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {
        "task_outcomes": [],
        "patterns": {},
        "suggestions": [],
        "last_analysis": None,
    }


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def analyze_outcomes(msgs):
    """Extract task outcomes from bus messages."""
    outcomes = []
    for m in msgs:
        if m.get("type") == "task_result":
            context = m.get("context") or {}
            outcomes.append({
                "task_id": context.get("task_id") or m.get("msg_id", "unknown"),
                "status": context.get("status", "unknown"),
                "from": m.get("from"),
                "timestamp": m.get("timestamp"),
                "msg_id": m.get("msg_id"),
            })
    return outcomes


def detect_patterns(outcomes):
    """Detect patterns in task outcomes."""
    patterns = {}
    
    # Success rate
    total = len(outcomes)
    successes = sum(1 for o in outcomes if o["status"] == "success")
    failures = sum(1 for o in outcomes if o["status"] in ("error", "failed", "timeout"))
    
    patterns["total_tasks"] = total
    patterns["success_count"] = successes
    patterns["failure_count"] = failures
    patterns["success_rate"] = successes / total if total > 0 else 0.0
    
    # By sender
    by_sender = Counter(o["from"] for o in outcomes)
    patterns["tasks_by_sender"] = dict(by_sender)
    
    # Error types
    errors = [o for o in outcomes if o["status"] != "success"]
    error_types = Counter(o["status"] for o in errors)
    patterns["error_types"] = dict(error_types)
    
    # Event type distribution
    return patterns


def generate_suggestions(patterns, outcomes):
    """Generate improvement suggestions based on patterns."""
    suggestions = []
    
    if patterns["total_tasks"] == 0:
        suggestions.append({
            "type": "initialization",
            "priority": "medium",
            "text": "No tasks completed yet. System needs real work to improve.",
        })
    
    if patterns["failure_count"] > 0:
        suggestions.append({
            "type": "reliability",
            "priority": "high",
            "text": f"{patterns['failure_count']} failures detected. Review error patterns and add retry logic.",
        })
    
    if patterns["success_rate"] > 0 and patterns["success_rate"] < 0.8:
        suggestions.append({
            "type": "quality",
            "priority": "high",
            "text": f"Success rate is {patterns['success_rate']:.0%}. Target >80%. Consider adding validation steps.",
        })
    
    if patterns["total_tasks"] > 10 and patterns["success_rate"] > 0.9:
        suggestions.append({
            "type": "expansion",
            "priority": "medium",
            "text": f"Success rate {patterns['success_rate']:.0%} over {patterns['total_tasks']} tasks. System is stable — consider expanding scope.",
        })
    
    # Dedup suggestions
    existing_types = {s["type"] for s in suggestions}
    if "improve_task_validation" not in existing_types and patterns["total_tasks"] > 0:
        suggestions.append({
            "type": "improve_task_validation",
            "priority": "low",
            "text": "Add pre-execution validation: check inputs before processing to catch errors early.",
        })
    
    if "add_metrics_logging" not in existing_types:
        suggestions.append({
            "type": "add_metrics_logging",
            "priority": "low",
            "text": "Log execution time per task to track performance trends over time.",
        })
    
    return suggestions


def run_analysis():
    """Run one analysis cycle."""
    msgs = load_bus_events()
    state = load_state()
    
    outcomes = analyze_outcomes(msgs)
    patterns = detect_patterns(outcomes)
    suggestions = generate_suggestions(patterns, outcomes)
    
    state["task_outcomes"] = outcomes
    state["patterns"] = patterns
    state["suggestions"] = suggestions
    state["last_analysis"] = datetime.now(timezone.utc).isoformat()
    
    save_state(state)
    
    print(f"Learning analysis complete:")
    print(f"  Tasks: {patterns['total_tasks']}")
    print(f"  Success rate: {patterns['success_rate']:.0%}")
    print(f"  Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"    [{s['priority']}] {s['text']}")
    
    return state


if __name__ == "__main__":
    run_analysis()
