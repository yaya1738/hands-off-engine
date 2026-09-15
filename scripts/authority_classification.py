#!/usr/bin/env python3
"""Classify a governed command and publish the observation on the canonical bus.

This bridge reuses the existing fail-closed authority seam. It never executes
work, opens the executor gate, or creates a second state store.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from autonomous.governed_authority import authorize
from scripts.comm_hub import CommHub

AUTHORITY_DECISION_EVENT = "authority_decision"


def classify_and_publish(
    command: Dict[str, Any],
    *,
    repo_root: Optional[Path] = None,
    execution_gate: bool | None = None,
) -> Dict[str, Any]:
    """Classify one command and publish its bounded decision to the canonical bus."""
    if not isinstance(command, dict):
        return {"status": "rejected", "reason": "invalid_command"}

    decision = authorize(command, execution_gate=execution_gate)
    correlation = command.get("correlation")
    if not isinstance(correlation, dict):
        correlation = {}

    decision_payload = decision.to_dict()
    decision_payload.update(
        {
            "msg_id": correlation.get("msg_id") or decision.command_id,
            "reply_to": correlation.get("reply_to"),
            "task_id": correlation.get("task_id"),
            "decided_at": None,
        }
    )

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent.parent
    result = CommHub(repo_root=root).receive(
        "factory",
        AUTHORITY_DECISION_EVENT,
        {"event_type": AUTHORITY_DECISION_EVENT, "decision": decision_payload},
        channel="messages_jsonl",
    )
    if result.get("routed_to") == "rejected":
        return {"status": "error", "reason": result.get("error", "rejected")}

    return {"status": "published", "decision": decision_payload}


__all__ = ["AUTHORITY_DECISION_EVENT", "classify_and_publish"]
