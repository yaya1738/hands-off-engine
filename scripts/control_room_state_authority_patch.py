#!/usr/bin/env python3
"""Compatibility-free authority observation helper for the shared snapshot."""
from __future__ import annotations

from typing import Any, Dict


def project_authority_decision(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the bounded authority decision already present in a snapshot."""
    if not isinstance(snapshot, dict):
        return {"available": False}
    decision = snapshot.get("authority_decision")
    if not isinstance(decision, dict) or decision.get("available") is False:
        return {"available": False}
    return {
        "available": True,
        "msg_id": decision.get("msg_id"),
        "reply_to": decision.get("reply_to"),
        "task_id": decision.get("task_id"),
        "decision": decision.get("decision"),
        "reason": decision.get("reason"),
        "approval_required": bool(decision.get("approval_required", True)),
        "execution_enabled": bool(decision.get("execution_enabled", False)),
        "decided_at": decision.get("decided_at"),
    }

__all__ = ["project_authority_decision"]
