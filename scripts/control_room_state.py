#!/usr/bin/env python3
"""Build a bounded read-only observability snapshot for the Control Room."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.interaction_thread_projection import project_threads
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
    return {task_id: {**entry, "current_state": current_state(entry)} for task_id, entry in items[:limit]}


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
    return {"available": True, "admitted_count": len(admissions), "rejected_count": len(rejections), "admissions": admissions[-limit:], "rejections": rejections[-limit:]}


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
    if not path.exists():
        return {"available": False}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {"available": False}
    if not isinstance(value, dict):
        return {"available": False}
    return {"available": True, "status": value.get("status"), "timestamp": value.get("timestamp"), "processed_commands": value.get("processed_commands", 0), "governed_decisions": value.get("governed_decisions", 0), "execution_enabled": False, "fail_closed": True}


def _correlation_health(events: List[dict], bus_limit: int, window_truncated: bool = False) -> Dict[str, Any]:
    """Summarize explicit correlation quality without inferring relationships."""
    msg_to_task: Dict[str, str] = {}
    msg_ids = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        context = event.get("context") or {}
        msg_id = event.get("msg_id")
        task_id = event.get("task_id") or context.get("task_id")
        if msg_id is not None:
            msg_ids.add(str(msg_id))
            if task_id is not None:
                msg_to_task[str(msg_id)] = str(task_id)

    correlated = orphan = single = explicit_task = 0
    thread_keys = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        context = event.get("context") or {}
        task_id = event.get("task_id") or context.get("task_id")
        reply_to = event.get("reply_to") or context.get("reply_to")
        if task_id is not None:
            explicit_task += 1
            correlated += 1
            thread_keys.add(f"task:{task_id}")
        elif reply_to is not None:
            target = str(reply_to)
            if target in msg_ids:
                correlated += 1
                target_task = msg_to_task.get(target)
                thread_keys.add(f"task:{target_task}" if target_task else f"reply:{target}")
            else:
                orphan += 1
        else:
            single += 1
            if event.get("msg_id") is not None:
                thread_keys.add(f"msg:{event['msg_id']}")

    event_count = len(events)
    return {
        "available": bool(events),
        "event_count": event_count,
        "thread_count": len(thread_keys),
        "correlated_event_count": correlated,
        "orphan_reply_count": orphan,
        "single_event_count": single,
        "explicit_task_event_count": explicit_task,
        "explicit_task_thread_coverage": (explicit_task / event_count) if event_count else None,
        "window": {"bounded": bus_limit > 0, "limit": bus_limit, "truncated": window_truncated},
    }


def _factory_assessment_observation(assessment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Project an already-produced Factory assessment without re-observing or mutating it."""
    if not isinstance(assessment, dict):
        return {"available": False}
    interaction = assessment.get("interaction_health", {})
    if not isinstance(interaction, dict):
        interaction = {}
    return {
        "available": True,
        "health": assessment.get("health"),
        "gaps": list(assessment.get("gaps", [])),
        "objective": assessment.get("objective"),
        "interaction_health": interaction,
    }


def build_snapshot(repo_root: Optional[Path] = None, bus_limit: int = 120, lifecycle_limit: int = 100, intake_limit: int = 20, thread_limit: int = 20, events_per_thread: int = 20, factory_assessment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return bounded bus + lifecycle + interaction state without executing or mutating work."""
    root = Path(repo_root) if repo_root else ROOT
    bus = root / "ai" / "coordination" / "messages.jsonl"
    lifecycle = root / "state" / "task_lifecycle.json"
    probe_limit = bus_limit + 1 if bus_limit > 0 else 0
    probed_events = _read_bus(bus, probe_limit)
    window_truncated = bus_limit > 0 and len(probed_events) > bus_limit
    events = probed_events[-bus_limit:] if bus_limit > 0 else []
    tasks = _read_lifecycle(lifecycle, lifecycle_limit)
    request_intake = root / "state" / "request_intake_state.json"
    factory_intake = root / "state" / "factory_intake_state.json"
    heartbeat = root / "state" / "dass_heartbeat_status.json"
    return {
        "source_of_truth": "ai/coordination/messages.jsonl",
        "bus": {"available": bus.exists(), "event_count": len(events), "events": events},
        "lifecycle": {"available": lifecycle.exists(), "task_count": len(tasks), "tasks": tasks},
        "threads": project_threads(events, tasks, limit=thread_limit, events_per_thread=events_per_thread),
        "correlation_health": _correlation_health(events, bus_limit, window_truncated),
        "factory_assessment": _factory_assessment_observation(factory_assessment),
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
