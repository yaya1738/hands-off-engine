#!/usr/bin/env python3
"""Lifecycle Trends — does the system improve over time?

Reads lifecycle projection, feedback history, learning state, and health log
to answer: is the hands-off engine getting better over days/weeks?

Outputs:
- Task throughput per period (by updated_at)
- Completion rate (tasks reaching result_published vs stuck in sent)
- State distribution trend over time windows
- Health trend (healthy checks vs issues)
- Improvement feedback trajectory (avg score over time)

Usage:
  python3 scripts/lifecycle_trends.py            — human summary
  python3 scripts/lifecycle_trends.py --json     — machine-readable
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
LIFECYCLE_FILE = STATE / "task_lifecycle.json"
FEEDBACK_HISTORY = STATE / "feedback_history.json"
HEALTH_LOG = STATE / "health_log.jsonl"
LEARNING_STATE = STATE / "learning_state.json"

STATE_ORDER = ("sent", "claimed", "executing", "completed", "result_published", "observed")


def _load_json(path):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _ts_iso(value):
    if not value:
        return ""
    if isinstance(value, dict):
        value = value.get("timestamp") or value.get("updated_at") or ""
    return str(value)


def _parse_period(value):
    """Return a coarse period bucket (day or hour) from an ISO timestamp."""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "unknown"


def current_state(entry):
    states = set(entry.get("states", {}).keys())
    for s in reversed(STATE_ORDER):
        if s in states:
            return s
    return "unknown"


def task_trends(lifecycle):
    """Per-day counts: tasks seen, completed (result_published), stuck (sent only)."""
    by_day = defaultdict(lambda: {"total": 0, "completed": 0, "stuck": 0})
    for task_id, entry in lifecycle.items():
        day = _parse_period(entry.get("updated_at", ""))
        by_day[day]["total"] += 1
        state = current_state(entry)
        if state == "result_published":
            by_day[day]["completed"] += 1
        elif state == "sent":
            by_day[day]["stuck"] += 1
    return dict(sorted(by_day.items()))


def state_distribution(lifecycle):
    counts = Counter(current_state(e) for e in lifecycle.values())
    return {s: counts.get(s, 0) for s in STATE_ORDER if counts.get(s, 0)}


def health_trends():
    rows = _load_jsonl(HEALTH_LOG)
    by_day = defaultdict(lambda: {"checks": 0, "healthy": 0})
    for r in rows:
        day = _parse_period(r.get("timestamp", r.get("checked_at", "")))
        by_day[day]["checks"] += 1
        if r.get("healthy", True):
            by_day[day]["healthy"] += 1
    result = {}
    for day, v in sorted(by_day.items()):
        result[day] = {
            "checks": v["checks"],
            "healthy": v["healthy"],
            "health_rate": round(v["healthy"] / max(v["checks"], 1), 3),
        }
    return result


def feedback_trajectory():
    history = _load_jsonl(FEEDBACK_HISTORY)
    points = []
    for h in history:
        day = _parse_period(h.get("timestamp", ""))
        avg = (h.get("summary") or {}).get("avg_score")
        if avg is not None:
            points.append({"day": day, "avg_score": avg})
    return points


def learning_summary():
    learning = _load_json(LEARNING_STATE)
    patterns = learning.get("patterns", {})
    return {
        "total_tasks": patterns.get("total_tasks", 0),
        "success_rate": round(patterns.get("success_rate", 0.0), 3),
        "failure_count": patterns.get("failure_count", 0),
        "error_types": patterns.get("error_types", {}),
    }


def build_trends():
    lifecycle = _load_json(LIFECYCLE_FILE)
    return {
        "task_count": len(lifecycle),
        "per_day": task_trends(lifecycle),
        "state_distribution": state_distribution(lifecycle),
        "health": health_trends(),
        "feedback_trajectory": feedback_trajectory(),
        "learning": learning_summary(),
    }


def render_human(trends):
    print("=== Task throughput by day ===")
    for day, v in trends["per_day"].items():
        print(f"  {day}: total={v['total']} completed={v['completed']} stuck={v['stuck']}")

    print("\n=== State distribution (current) ===")
    for s, c in trends["state_distribution"].items():
        print(f"  {s:<16} {c}")

    print("\n=== Health trend ===")
    for day, h in trends["health"].items():
        icon = "✅" if h["health_rate"] >= 0.9 else ("⚠️" if h["health_rate"] >= 0.5 else "❌")
        print(f"  {day}: {icon} {h['healthy']}/{h['checks']} healthy ({h['health_rate']:.0%})")

    print("\n=== Improvement feedback trajectory ===")
    pts = trends["feedback_trajectory"]
    if pts:
        for p in pts:
            icon = "✅" if p["avg_score"] > 0.1 else ("❌" if p["avg_score"] < -0.1 else "➖")
            print(f"  {p['day']}: {icon} avg score {p['avg_score']:+.3f}")
    else:
        print("  No feedback trajectory yet")

    print("\n=== Learning state ===")
    learn = trends["learning"]
    print(f"  Tasks: {learn['total_tasks']} | success rate: {learn['success_rate']:.0%} | failures: {learn['failure_count']}")
    for etype, count in (learn.get("error_types") or {}).items():
        print(f"  error[{etype}]: {count}")


def main():
    parser = argparse.ArgumentParser(description="Lifecycle + health trend analysis")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    trends = build_trends()
    if args.json:
        print(json.dumps(trends, indent=2, default=str))
    else:
        render_human(trends)


if __name__ == "__main__":
    main()
