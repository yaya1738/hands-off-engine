"""Pure, bounded correlation projection for canonical interaction events."""
from __future__ import annotations

from typing import Any, Dict, List


def _field(event: dict, name: str) -> Any:
    value = event.get(name)
    if value is not None:
        return value
    context = event.get("context")
    if isinstance(context, dict):
        return context.get(name)
    return None


def project_threads(events: List[dict], lifecycle: Dict[str, dict], limit: int = 20, events_per_thread: int = 20) -> List[dict]:
    """Return bounded threads using explicit IDs only, independent of order."""
    if limit <= 0 or events_per_thread <= 0:
        return []

    by_msg: Dict[str, dict] = {}
    msg_to_task: Dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        msg_id = _field(event, "msg_id")
        task_id = _field(event, "task_id")
        if msg_id is not None:
            key = str(msg_id)
            by_msg[key] = event
            if task_id is not None:
                msg_to_task[key] = str(task_id)

    groups: Dict[str, List[dict]] = {}
    order: List[str] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        msg_id = _field(event, "msg_id")
        task_id = _field(event, "task_id")
        reply_to = _field(event, "reply_to")
        msg_key = str(msg_id) if msg_id is not None else f"event-{index}"

        if task_id is not None:
            key, kind, quality = f"task:{task_id}", "task", "correlated"
        elif reply_to is not None and str(reply_to) in by_msg:
            target_task = msg_to_task.get(str(reply_to))
            key = f"task:{target_task}" if target_task else f"reply:{reply_to}"
            kind, quality = "reply", "correlated"
        elif reply_to is not None:
            key, kind, quality = f"orphan:{msg_key}", "reply", "orphan_reply"
        else:
            key, kind, quality = f"msg:{msg_key}", "message", "single_event"

        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append({**event, "_correlation_quality": quality, "_correlation_kind": kind})

    threads: List[dict] = []
    for key in order[-limit:]:
        entries = groups[key][-events_per_thread:]
        for entry in entries:
            entry.pop("_correlation_kind", None)
            entry["correlation_quality"] = entry.pop("_correlation_quality", "single_event")
        task_ids = [str(_field(event, "task_id")) for event in entries if _field(event, "task_id") is not None]
        task_id = task_ids[-1] if task_ids else (msg_to_task.get(str(_field(entries[-1], "reply_to"))) if entries else None)
        lifecycle_state = lifecycle.get(task_id, {}).get("current_state") if task_id and isinstance(lifecycle.get(task_id), dict) else None
        qualities = {entry.get("correlation_quality") for entry in entries}
        quality = "orphan_reply" if "orphan_reply" in qualities else ("correlated" if "correlated" in qualities else "single_event")
        threads.append({
            "correlation_key": key,
            "correlation_kind": "task" if key.startswith("task:") else ("reply" if key.startswith("reply:") or key.startswith("orphan:") else "message"),
            "events": entries,
            "task_id": task_id,
            "lifecycle_state": lifecycle_state,
            "correlation_quality": quality,
        })
    return threads
