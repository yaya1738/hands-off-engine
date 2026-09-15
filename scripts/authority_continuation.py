#!/usr/bin/env python3
"""Turn an observed authority approval into a bounded canonical continuation event."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scripts.comm_hub import CommHub

CONTINUATION_EVENT = "authority_continuation"


def continue_from_authority(
    snapshot: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Publish continuation only for an explicitly approved observed request.

    This is a routing adapter, not an executor. It never enables LIVE execution.
    """
    if not isinstance(snapshot, dict):
        return {"status": "skipped", "reason": "invalid_snapshot"}
    decision = snapshot.get("authority_decision")
    if not isinstance(decision, dict) or not decision.get("available", False):
        return {"status": "skipped", "reason": "no_authority_decision"}
    if decision.get("decision") != "approved":
        return {"status": "skipped", "reason": "not_approved"}

    msg_id = decision.get("msg_id")
    task_id = decision.get("task_id")
    if not msg_id or not task_id:
        return {"status": "skipped", "reason": "missing_correlation"}

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent.parent
    payload = {
        "event_type": CONTINUATION_EVENT,
        "continuation": {
            "msg_id": str(msg_id),
            "reply_to": decision.get("reply_to") or msg_id,
            "task_id": str(task_id),
            "decision": "approved",
            "execution_enabled": False,
        },
    }
    result = CommHub(repo_root=root).receive(
        "factory",
        CONTINUATION_EVENT,
        payload,
        channel="messages_jsonl",
    )
    if result.get("routed_to") == "rejected":
        return {"status": "error", "reason": result.get("error", "rejected")}
    return {"status": "published", "msg_id": str(msg_id), "task_id": str(task_id)}


__all__ = ["CONTINUATION_EVENT", "continue_from_authority"]
