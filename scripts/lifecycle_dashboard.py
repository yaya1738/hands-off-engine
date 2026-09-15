#!/usr/bin/env python3
"""Lifecycle Dashboard — machine + human readable view of task lifecycle.

Reads state/task_lifecycle.json (projection of the canonical bus) and renders:
- per-task state chart (current state, timestamps, sender/recipient/action)
- state distribution summary (how many tasks in each phase)
- per-party activity (senders/recipients)
- optional JSON export for other agents/nodes

Usage:
  python3 scripts/lifecycle_dashboard.py            — human table
  python3 scripts/lifecycle_dashboard.py --json     — machine-readable JSON
  python3 scripts/lifecycle_dashboard.py --task <id>— single task detail
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
LIFECYCLE_FILE = STATE / "task_lifecycle.json"

STATE_ORDER = ("sent", "claimed", "executing", "completed", "result_published", "observed")
STATE_EMOJI = {
    "sent": "📨", "claimed": "🤝", "executing": "⚙️", "completed": "✅",
    "result_published": "📤", "observed": "👁️",
}


def load_lifecycle(path: Path = LIFECYCLE_FILE) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def current_state(entry: dict) -> str:
    states = set(entry.get("states", {}).keys())
    for state in reversed(STATE_ORDER):
        if state in states:
            return state
    return "unknown"


def build_rows(lifecycle: dict) -> list:
    rows = []
    for task_id, entry in lifecycle.items():
        states = entry.get("states", {})
        current = current_state(entry)
        then = states.get(current, "")
        rows.append({
            "task_id": task_id,
            "current": current,
            "state_at": then,
            "sender": entry.get("sender", ""),
            "recipient": entry.get("recipient", ""),
            "action": entry.get("action", ""),
            "correlation": entry.get("correlation_id", ""),
            "updated_at": entry.get("updated_at", ""),
            "status": entry.get("status", ""),
        })
    rows.sort(key=lambda r: r["updated_at"], reverse=True)
    return rows


def render_human(rows, limit=30):
    if not rows:
        print("No lifecycle entries yet — run scripts/lifecycle_projection.py first")
        return
    print(f"{'STATE':<16} {'TASK ID':<28} {'ACTION':<16} {'SENDER':<10} {'RECIP':<10} UPDATED")
    print("-" * 100)
    for r in rows[:limit]:
        emoji = STATE_EMOJI.get(r["current"], "•")
        action = (r["action"] or "—")[:14]
        print(f"{emoji} {r['current']:<14} {r['task_id'][:26]:<28} {action:<16} "
              f"{r['sender'][:8]:<10} {r['recipient'][:8]:<10} {r['updated_at'][5:19]}")


def render_summary(rows):
    if not rows:
        return
    counts = Counter(r["current"] for r in rows)
    by_sender = Counter(r["sender"] for r in rows)
    by_recipient = Counter(r["recipient"] for r in rows)
    print("\n=== State distribution ===")
    for state in STATE_ORDER:
        c = counts.get(state, 0)
        if c:
            print(f"  {STATE_EMOJI.get(state,'•')} {state:<16} {c}")
    print(f"\n=== Party activity (sender) ===")
    for party, c in by_sender.most_common(8):
        print(f"  {party:<14} {c}")
    print(f"\n=== Party activity (recipient) ===")
    for party, c in by_recipient.most_common(8):
        print(f"  {party:<14} {c}")


def render_json(rows):
    summary = {}
    counts = Counter(r["current"] for r in rows)
    summary["task_count"] = len(rows)
    summary["by_state"] = dict(counts)
    summary["by_sender"] = dict(Counter(r["sender"] for r in rows))
    summary["by_recipient"] = dict(Counter(r["recipient"] for r in rows))
    print(json.dumps({"summary": summary, "tasks": rows}, indent=2, default=str))


def task_detail(lifecycle, task_id):
    entry = lifecycle.get(task_id)
    if entry is None:
        print(f"Task not found: {task_id}")
        return
    print(json.dumps(entry, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Lifecycle dashboard")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--task", default=None, help="show single task detail")
    parser.add_argument("--limit", type=int, default=30, help="max rows (human view)")
    parser.add_argument("--file", default=None, help="lifecycle file (default state/task_lifecycle.json)")
    args = parser.parse_args()

    lifecycle = load_lifecycle(args.file and Path(args.file) or LIFECYCLE_FILE)

    if args.task:
        task_detail(lifecycle, args.task)
        return

    rows = build_rows(lifecycle)
    if args.json:
        render_json(rows)
    else:
        render_human(rows, args.limit)
        render_summary(rows)


if __name__ == "__main__":
    main()
