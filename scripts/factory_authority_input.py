#!/usr/bin/env python3
"""Build a bounded authority command from shared Factory decision context.

This adapter translates observation into the existing governed-authority input
shape. It does not authorize, persist, route, or execute work.
"""
from __future__ import annotations

from typing import Any, Dict


def build_authority_input(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a fail-closed DRYRUN command suitable for authority classification."""
    if not isinstance(context, dict) or not context.get("available", False):
        return {"available": False}

    authority = context.get("authority")
    admission = context.get("admission")
    assessment = context.get("assessment")
    if not isinstance(authority, dict):
        authority = {}
    if not isinstance(admission, dict):
        admission = {}
    if not isinstance(assessment, dict):
        assessment = {}

    msg_id = authority.get("msg_id") or admission.get("msg_id")
    task_id = authority.get("task_id") or admission.get("task_id")
    objective = assessment.get("objective")
    if not objective or not isinstance(objective, str):
        return {"available": False}

    command_id = str(msg_id or task_id or "")
    if not command_id:
        return {"available": False}

    return {
        "available": True,
        "command": {
            "id": command_id,
            "mode": "DRYRUN",
            "approval_status": "pending",
            "objective": objective,
            "priority": assessment.get("health", 0),
            "correlation": {
                "msg_id": str(msg_id) if msg_id else None,
                "task_id": str(task_id) if task_id else None,
                "reply_to": authority.get("reply_to") or admission.get("reply_to"),
            },
        },
    }


__all__ = ["build_authority_input"]
