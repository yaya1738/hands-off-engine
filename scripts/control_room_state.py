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
    """Build bounded threads from explicit IDs only.

    task_id is authoritative when present. reply_to links only to an observed
    msg_id, and the target's explicit task_id wins when that target belongs to
    a task. Relationships are resolved independent of event ordering; no
    proximity or message-text inference is used. Read-only; no routing/mutation.
    """
    if limit <= 0:
        return {"available": bool(events), "count": 0, "threads": []}

    msg_to_task: Dict[str, str] = {}
    msg_ids = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        context = event.get("context") or {}
        msg_id = event.get("msg_id")
        task_id = event.get("task_id") or context.get("task_id")
        if msg_id:
            msg_ids.add(str(msg_id))
            if task_id:
                msg_to_task[str(msg_id)] = str(task_id)

    def target_key(reply_to: Any) -> Optional[str]:
        if reply_to is None:
            return None
        target = str(reply_to)
        if target not in msg_ids:
            return None
        task_id = msg_to_task.get(target)
        return f"task:{task_id}" if task_id else f"msg:{target}"

    threads: Dict[str, dict] = {}
    order: List[str] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        context = event.get("context") or {}
        msg_id = event.get("msg_id")
        task_id = event.get("task_id") or context.get("task_id")
        reply_to = event.get("reply_to") or context.get("reply_to")

        if task_id:
            key = f"task:{task_id}"
            quality = "correlated"
        else:
            key = target_key(reply_to)
            if key is not None:
                quality = "correlated"
            elif reply_to is not None:
                key = f"orphan:{msg_id or f'event-{index + 1}'}"
                quality = "orphan_reply"
            elif msg_id:
                key = f"msg:{msg_id}"
                quality = "single_event"
            else:
                key = f"unknown:{index + 1}"
                quality = "single_event"

        if key not in threads:
            threads[key] = {"key": key, "events": [], "correlation_quality": quality}
            order.append(key)
        entry = {
            "msg_id": msg_id or "unknown",
            "type": event.get("type", "unknown"),
            "timestamp": event.get("timestamp", ""),
            "task_id": task_id or "unknown",
            "reply_to": reply_to or "unknown",
            "lifecycle_state": (lifecycle_tasks.get(str(task_id)) or {}).get("current_state", "unknown") if task_id else "unknown",
            "correlation_quality": quality,
        }
        threads[key]["events"].append(entry)
        if quality == "correlated":
            threads[key]["correlation_quality"] = "correlated"

    out = [threads[key] for key in order[-limit:]]
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
        "bus": {"available": bus.exists(), "event_count": len(events), "events": events},
        "lifecycle": {"available": lifecycle.exists(), "task_count": len(tasks), "tasks": tasks},
        "intake": {"request": _read_request_intake(request_intake, intake_limit), "factory": _read_factory_intake(factory_intake, intake_limit)},
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
