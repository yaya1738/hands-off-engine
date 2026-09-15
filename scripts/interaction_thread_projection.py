"""Pure, bounded correlation projection for canonical interaction events.

This module never writes to the coordination bus or lifecycle state. It only
interprets explicit correlation identifiers already present in events.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _field(event: dict, name: str) -> Any:
    value = event.get(name)
    if value is not None:
        return value
    context = event.get("context")
    if isinstance(context, dict):
        return context.get(name)
    return None


def project_threads(events: List[dict], lifecycle: Dict[str, dict], limit: int = 20, events_per_thread: int = 20) -> List[dict]:
    """Return bounded threads using explicit IDs only; never infer by proximity/text."""
    if limit <= 0 or events_per_thread <= 0:
        return []

    # Order-independent resolution: an event's msg_id/task_id map is built
    # across the whole bounded window before grouping, so a reply links to its
    # referenced message regardless of event ordering (never from proximity).
    msg_ids: set = set()
    msg_to_task: Dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        msg_id = _field(event, "msg_id")
        task_id = _field(event, "task_id")
        if msg_id is not None:
            msg_ids.add(str(msg_id))
            if task_id is not None:
                msg_to_task[str(msg_id)] = str(task_id)

    def target_key(reply_to: Any) -> Optional[str]:
        if reply_to is None:
            return None
        target = str(reply_to)
        if target not in msg_ids:
            return None
        task_id = msg_to_task.get(target)
        return f"task:{task_id}" if task_id else f"msg:{target}"

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
            key = f"task:{task_id}"
            quality = "correlated"
        else:
            linked = target_key(reply_to)
            if linked is not None:
                key, quality = linked, "correlated"
            elif reply_to is not None:
                key, quality = f"orphan:{msg_key}", "orphan_reply"
            else:
                key, quality = f"msg:{msg_key}", "single_event"

        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append({**event, "_index": index, "_correlation_quality": quality})

    for key, entries in groups.items():
        for entry in entries:
            entry.pop("_index", None)
            entry_quality = entry.pop("_correlation_quality", "single_event")
            entry["correlation_quality"] = entry_quality

    threads: List[dict] = []
    for key in order[-limit:]:
        entries = groups[key][-events_per_thread:]
        task_ids = [str(_field(event, "task_id")) for event in entries if _field(event, "task_id") is not None]
        task_id = task_ids[-1] if task_ids else None
        lifecycle_state = None
        if task_id and isinstance(lifecycle.get(task_id), dict):
            lifecycle_state = lifecycle[task_id].get("current_state")
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
