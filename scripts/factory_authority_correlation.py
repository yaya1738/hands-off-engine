#!/usr/bin/env python3
"""Validate correlation continuity across a governed authority decision."""
from __future__ import annotations

from typing import Any, Dict


def correlate_authority_decision(
    proposal: Dict[str, Any], decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Return explicit identity continuity; never infer identity from text."""
    if not isinstance(proposal, dict) or not isinstance(decision, dict):
        return {"available": False}

    proposal_body = proposal.get("proposal")
    if not isinstance(proposal_body, dict):
        return {"available": False}

    proposal_msg = proposal_body.get("msg_id")
    proposal_task = proposal_body.get("task_id")
    decision_msg = decision.get("msg_id")
    decision_task = decision.get("task_id")

    if not proposal_msg and not proposal_task:
        return {"available": False}

    msg_match = proposal_msg is not None and proposal_msg == decision_msg
    task_match = proposal_task is not None and proposal_task == decision_task

    return {
        "available": True,
        "msg_id": decision_msg,
        "task_id": decision_task,
        "msg_id_match": msg_match,
        "task_id_match": task_match,
        "correlated": bool(msg_match or task_match),
    }


__all__ = ["correlate_authority_decision"]
