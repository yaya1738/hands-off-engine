#!/usr/bin/env python3
"""Read-only governed continuation observation from the shared snapshot."""
from __future__ import annotations

from typing import Any, Dict


def project_authority_continuation(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Expose whether an explicit approved decision permits continuation.

    This is an observation only. It never authorizes execution and never writes
    lifecycle state. The executor gate remains a separate boundary.
    """
    if not isinstance(snapshot, dict):
        return {"available": False, "continuation_allowed": False}

    decision = snapshot.get("authority_decision")
    if not isinstance(decision, dict) or not decision.get("available", False):
        return {"available": False, "continuation_allowed": False}

    approved = decision.get("decision") == "approved"
    return {
        "available": True,
        "msg_id": decision.get("msg_id"),
        "reply_to": decision.get("reply_to"),
        "task_id": decision.get("task_id"),
        "decision": decision.get("decision"),
        "approval_required": bool(decision.get("approval_required", True)),
        "execution_enabled": False,
        "continuation_allowed": approved,
    }


__all__ = ["project_authority_continuation"]
