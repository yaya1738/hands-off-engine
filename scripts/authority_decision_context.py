#!/usr/bin/env python3
"""Derive a read-only continuation signal from shared authority observation."""
from __future__ import annotations

from typing import Any, Dict


def build_authority_continuation_context(snapshot: Dict[str, Any]) -> Dict[str, Any]:
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
        "execution_enabled": bool(decision.get("execution_enabled", False)),
        "continuation_allowed": approved,
    }

__all__ = ["build_authority_continuation_context"]
