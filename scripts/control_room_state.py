#!/usr/bin/env python3
"""Build a bounded read-only observability snapshot for the Control Room.

The canonical coordination bus remains the source of truth. Task lifecycle
state is only a durable projection, so operators and agents can inspect both
views without introducing another transport or mutating execution state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lifecycle_dashboard import current_state


def _read_bus(path: Path, limit: int) -> List[dict]:
    if not path.exists() or limit <= 0:
        return []
    rows: List[dict] = []
    with path.open("rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        carry = b""
        while position > 0 and len(rows) < limit:
            size = min(8192, position)
            position -= size
            handle.seek(position)
            chunk = handle.read(size)
            data = chunk + carry
            parts = data.split(b"\n")
            carry = parts.pop(0)
            for line in reversed(parts):
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if isinstance(value, dict):
                    rows.append(value)
                    if len(rows) >= limit:
                        break
    if carry and len(rows) < limit:
        try:
            value = json.loads(carry)
        except (json.JSONDecodeError, UnicodeDecodeError):
            value = None
        if isinstance(value, dict):
            rows.append(value)
    rows.reverse()
    return rows


def _read_lifecycle(path: Path, limit: int) -> Dict[str, dict]:
    if not path.exists() or limit <= 0:
        return {}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    items = [(str(k), v) for k, v in value.items() if isinstance(v, dict)]
    items.sort(key=lambda item: (str(item[1].get("updated_at", "")), item[0]), reverse=True)
    return {
        task_id: {**entry, "current_state": current_state(entry)}
        for task_id, entry in items[:limit]
    }


def _read_request_intake(path: Path, limit: int) -> Dict[str, Any]:
    if not path.exists() or limit <= 0:
        return {"available": False, "admitted_count": 0, "rejected_count": 0, "admissions": [], "rejections": []}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {"available": False, "admitted_count": 0, "rejected_count": 0, "admissions": [], "rejections": []}
    if not isinstance(value, dict):
        return {"available": False, "admitted_count": 0, "rejected_count": 0, "admissions": [], "rejections": []}
    admissions = value.get("admissions") or []
    rejections = value.get("rejections") or []
    if not isinstance(admissions, list) or not isinstance(rejections, list):
        return {"available": True, "admitted_count": 0, "rejected_count": 0, "admissions": [], "rejections": []}
    return {
        "available": True,
        "admitted_count": len(admissions),
        "rejected_count": len(rejections),
        "admissions": admissions[-limit:],
        "rejections": rejections[-limit:],
    }


def _read_factory_intake(path: Path, limit: int) -> Dict[str, Any]:
    if not path.exists() or limit <= 0:
        return {"available": False, "decision_count": 0, "decisions": []}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {"available": False, "decision_count": 0, "decisions": []}
    if not isinstance(value, dict):
        return {"available": False, "decision_count": 0, "decisions": []}
    decisions = value.get("decisions") or []
    if not isinstance(decisions, list):
        return {"available": True, "decision_count": 0, "decisions": []}
    return {"available": True, "decision_count": len(decisions), "decisions": decisions[-limit:]}


def _read_dass_heartbeat(path: Path) -> Dict[str, Any]:
    """Expose heartbeat status as read-only telemetry; never infer authority."""
    if not path.exists():
        return {"available": False}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {"available": False}
    if not isinstance(value, dict):
        return {"available": False}
    return {
        "available": True,
        "status": value.get("status"),
        "timestamp": value.get("timestamp"),
        "processed_commands": value.get("processed_commands", 0),
        "governed_decisions": value.get("governed_decisions", 0),
        "execution_enabled": False,
        "fail_closed": True,
    }


def _build_threads(events: List[dict], lifecycle_tasks: Dict[str, dict], limit: int = 10) -> Dict[str, Any]:
    """Build a bounded thread view using only explicitly observed ids.

    Threads are joined exclusively on msg_id / task_id / reply_to equality;
    relationships are never inferred from ordering or message text. Missing
    identifiers render as "unknown". Read-only; no routing or mutation.
    """
    known_ids = set()
    for event in events:
        context = event.get("context") or {}
        if event.get("msg_id"):
            known_ids.add(event["msg_id"])
        if context.get("task_id"):
            known_ids.add(context["task_id"])

    threads: Dict[str, dict] = {}
    order: List[str] = []
    for event in events:
        context = event.get("context") or {}
        mid = event.get("msg_id")
        tid = context.get("task_id")
        reply = context.get("reply_to")
        if reply and reply in known_ids:
            key = reply
        elif tid and tid in known_ids:
            key = tid
        elif mid:
            key = mid
        else:
            key = f"unknown-{len(order) + 1}"
        if key not in threads:
            threads[key] = {"key": key, "events": []}
            order.append(key)
        entry = {
            "msg_id": mid or "unknown",
            "type": event.get("type", "unknown"),
            "timestamp": event.get("timestamp", ""),
            "task_id": tid or "unknown",
            "reply_to": reply or "unknown",
            "lifecycle_state": (lifecycle_tasks.get(tid) or lifecycle_tasks.get(mid) or {}).get("current_state", "unknown"),
        }
        threads[key]["events"].append(entry)

    out = []
    for key in order:
        out.append(threads[key])
        if len(out) >= limit:
            break
    return {
        "available": bool(events),
        "count": len(out),
        "threads": out,
    }


def build_snapshot(repo_root: Optional[Path] = None, bus_limit: int = 120, lifecycle_limit: int = 100, intake_limit: int = 20, thread_limit: int = 10) -> Dict[str, Any]:
    """Return bounded bus + lifecycle state without executing or mutating work."""
    root = Path(repo_root) if repo_root else ROOT
    bus = root / "ai" / "coordination" / "messages.jsonl"
    lifecycle = root / "state" / "task_lifecycle.json"
    events = _read_bus(bus, bus_limit)
    tasks = _read_lifecycle(lifecycle, lifecycle_limit)
    request_intake = root / "state" / "request_intake_state.json"
    factory_intake = root / "state" / "factory_intake_state.json"
    heartbeat = root / "state" / "dass_heartbeat_status.json"
    return {
        "threads": _build_threads(events, tasks, thread_limit),
        "source_of_truth": "ai/coordination/messages.jsonl",
        "bus": {
            "available": bus.exists(),
            "event_count": len(events),
            "events": events,
        },
        "lifecycle": {
            "available": lifecycle.exists(),
            "task_count": len(tasks),
            "tasks": tasks,
        },
        "intake": {
            "request": _read_request_intake(request_intake, intake_limit),
            "factory": _read_factory_intake(factory_intake, intake_limit),
        },
        "heartbeat": _read_dass_heartbeat(heartbeat),
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Print bounded Control Room observability state")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--bus-limit", type=int, default=120)
    parser.add_argument("--lifecycle-limit", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(build_snapshot(args.repo_root, args.bus_limit, args.lifecycle_limit), indent=2, sort_keys=True))


if __name__ == "__main__": main()
