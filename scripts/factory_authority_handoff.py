#!/usr/bin/env python3
"""Translate a governed Factory handoff into the existing authority input.

This is an adapter only. It does not call the authority function, publish to
any bus, approve work, or enable execution.
"""
from __future__ import annotations

from typing import Any, Dict

from autonomous.governed_authority import authorize


def build_authority_input(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """Return the minimal explicit authority input, fail-closed."""
    if not isinstance(handoff, dict) or not handoff.get("available", False):
        return {"available": False}

    body = handoff.get("handoff")
    if not isinstance(body, dict) or not body.get("requires_governance", False):
        return {"available": False}

    objective = body.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        return {"available": False}

    return {
        "available": True,
        "command": {
            "id": body.get("msg_id") or body.get("task_id") or "",
            "mode": "DRYRUN",
            "approval_status": "pending",
            "objective": objective,
            "correlation": {
                "msg_id": body.get("msg_id"),
                "reply_to": body.get("reply_to"),
                "task_id": body.get("task_id"),
            },
        },
    }


def classify_authority_input(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """Classify the adapter output through the existing authority seam."""
    projected = build_authority_input(handoff)
    if not projected.get("available", False):
        return {"available": False}

    decision = authorize(projected["command"])
    return {"available": True, "decision": decision.to_dict()}


__all__ = ["build_authority_input", "classify_authority_input"]
