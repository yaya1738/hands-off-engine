#!/usr/bin/env python3
"""Read-only admission-decision observation from the canonical coordination bus.

Admission decisions are observed only when they have been explicitly published
as canonical bus records. No inference from request proximity or local intake
state is performed.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable


ADMISSION_EVENT = "task_admission"


def latest_admission_decision(events: Iterable[dict]) -> Dict[str, Any]:
    """Return the latest explicit admission decision, or fail closed."""
    for event in reversed(list(events)):
        if not isinstance(event, dict):
            continue

        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("event_type") != ADMISSION_EVENT:
            continue

        decision = payload.get("decision")
        if not isinstance(decision, dict):
            continue

        msg_id = decision.get("msg_id")
        if not msg_id:
            continue

        return {
            "available": True,
            "msg_id": msg_id,
            "reply_to": decision.get("reply_to"),
            "task_id": decision.get("task_id"),
            "admitted": bool(decision.get("admitted", False)),
            "reason": decision.get("reason"),
            "decided_at": decision.get("decided_at"),
        }

    return {"available": False}


__all__ = ["ADMISSION_EVENT", "latest_admission_decision"]
