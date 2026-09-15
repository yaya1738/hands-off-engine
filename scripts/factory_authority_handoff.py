#!/usr/bin/env python3
"""Translate a governed Factory handoff into the existing authority input.

This adapter preserves the single authority publication path. It does not
approve work or enable execution itself.
"""
from __future__ import annotations

from typing import Any, Dict

from scripts.authority_classification import classify_and_publish


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

    correlation = {
        "msg_id": body.get("msg_id"),
        "reply_to": body.get("reply_to"),
        "task_id": body.get("task_id"),
    }
    command_id = correlation["msg_id"] or correlation["task_id"] or ""
    return {
        "available": True,
        "command": {
            "id": command_id,
            "mode": "DRYRUN",
            "approval_status": "pending",
            "objective": objective,
            "correlation": correlation,
        },
    }


def classify_authority_input(handoff: Dict[str, Any], *, repo_root=None) -> Dict[str, Any]:
    """Classify and publish through the established canonical authority bridge."""
    projected = build_authority_input(handoff)
    if not projected.get("available", False):
        return {"available": False}
    return classify_and_publish(projected["command"], repo_root=repo_root)


__all__ = ["build_authority_input", "classify_authority_input"]
