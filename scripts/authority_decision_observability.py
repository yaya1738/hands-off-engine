#!/usr/bin/env python3
"""Read-only authority-decision projection from the canonical bus."""
from __future__ import annotations

from typing import Any, Dict, Iterable

AUTHORITY_DECISION_EVENT = "authority_decision"


def latest_authority_decision(events: Iterable[dict]) -> Dict[str, Any]:
    """Return the latest explicit authority decision, fail-closed and bounded."""
    for event in reversed(list(events)):
        if not isinstance(event, dict):
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("event_type") != AUTHORITY_DECISION_EVENT:
            continue
        decision = payload.get("decision")
        if not isinstance(decision, dict) or not decision.get("msg_id"):
            continue
        return {
            "available": True,
            "msg_id": str(decision.get("msg_id")),
            "reply_to": decision.get("reply_to"),
            "task_id": decision.get("task_id"),
            "decision": decision.get("decision"),
            "reason": decision.get("reason"),
            "approval_required": bool(decision.get("approval_required", True)),
            "execution_enabled": bool(decision.get("execution_enabled", False)),
            "decided_at": decision.get("decided_at"),
        }
    return {"available": False}


__all__ = ["AUTHORITY_DECISION_EVENT", "latest_authority_decision"]
