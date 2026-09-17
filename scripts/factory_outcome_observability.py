#!/usr/bin/env python3
"""Project bounded task outcomes for Factory learning.

This helper consumes already-read canonical bus events. It does not persist,
route, authorize, execute, or infer relationships from message text.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def project_factory_outcomes(events: Iterable[dict], limit: int = 20) -> Dict[str, Any]:
    """Return bounded explicit task-result observations, fail-closed."""
    if limit <= 0:
        return {"available": False, "outcome_count": 0, "outcomes": []}

    outcomes: List[Dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "task_result":
            continue
        context = event.get("context")
        if not isinstance(context, dict):
            context = {}
        task_id = context.get("task_id") or event.get("task_id")
        msg_id = event.get("msg_id")
        reply_to = event.get("reply_to") or context.get("reply_to")
        if task_id is None and msg_id is None:
            continue
        outcomes.append({
            "msg_id": msg_id,
            "task_id": task_id,
            "reply_to": reply_to,
            "status": context.get("status", event.get("status", "unknown")),
            "timestamp": event.get("timestamp"),
        })

    bounded = outcomes[-limit:]
    return {
        "available": bool(bounded),
        "outcome_count": len(bounded),
        "outcomes": bounded,
    }


__all__ = ["project_factory_outcomes"]
