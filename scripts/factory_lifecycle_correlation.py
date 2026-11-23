#!/usr/bin/env python3
"""Project explicit lifecycle identity for a governed interaction.

This is a read-only correlation helper. Lifecycle state remains a derived
projection of the canonical coordination bus; this module does not persist or
mutate lifecycle state.
"""
from __future__ import annotations

from typing import Any, Dict


def correlate_lifecycle(proposal: Dict[str, Any], lifecycle: Dict[str, Any]) -> Dict[str, Any]:
    """Return explicit msg/task/reply identity continuity, fail-closed."""
    if not isinstance(proposal, dict) or not isinstance(lifecycle, dict):
        return {"available": False}

    body = proposal.get("proposal")
    if not isinstance(body, dict):
        return {"available": False}

    proposal_msg = body.get("msg_id")
    proposal_task = body.get("task_id")
    lifecycle_msg = lifecycle.get("msg_id")
    lifecycle_task = lifecycle.get("task_id")
    lifecycle_reply = lifecycle.get("reply_to")

    if not proposal_msg and not proposal_task:
        return {"available": False}

    msg_match = proposal_msg is not None and proposal_msg == lifecycle_msg
    task_match = proposal_task is not None and proposal_task == lifecycle_task

    return {
        "available": True,
        "msg_id": lifecycle_msg,
        "task_id": lifecycle_task,
        "reply_to": lifecycle_reply,
        "msg_id_match": msg_match,
        "task_id_match": task_match,
        "correlated": bool(msg_match or task_match),
    }


__all__ = ["correlate_lifecycle"]
