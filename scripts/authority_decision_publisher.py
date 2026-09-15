#!/usr/bin/env python3
"""Publish explicit authority decisions through the canonical coordination bus."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.comm_hub import CommHub

AUTHORITY_DECISION_EVENT = "authority_decision"


def _already_published(messages_file: Path, msg_id: str) -> bool:
    if not messages_file.exists():
        return False
    try:
        for line in messages_file.read_text().splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload")
            decision = payload.get("decision") if isinstance(payload, dict) else None
            if (
                isinstance(payload, dict)
                and payload.get("event_type") == AUTHORITY_DECISION_EVENT
                and isinstance(decision, dict)
                and decision.get("msg_id") == msg_id
            ):
                return True
    except OSError:
        return False
    return False


def publish_authority_decision(
    decision: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Publish a bounded authority decision; never execute or approve work."""
    if not isinstance(decision, dict) or not decision.get("msg_id"):
        return {"status": "skipped", "reason": "invalid_decision"}

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent.parent
    messages_file = root / "ai" / "coordination" / "messages.jsonl"
    msg_id = str(decision["msg_id"])

    if _already_published(messages_file, msg_id):
        return {"status": "already_published", "msg_id": msg_id}

    payload = {
        "event_type": AUTHORITY_DECISION_EVENT,
        "decision": {
            "msg_id": msg_id,
            "reply_to": decision.get("reply_to"),
            "task_id": decision.get("task_id"),
            "decision": decision.get("decision", "denied"),
            "reason": decision.get("reason"),
            "approval_required": bool(decision.get("approval_required", True)),
            "execution_enabled": bool(decision.get("execution_enabled", False)),
            "decided_at": decision.get("decided_at"),
        },
    }

    result = CommHub(repo_root=root).receive(
        "factory",
        AUTHORITY_DECISION_EVENT,
        payload,
        channel="messages_jsonl",
    )
    if result.get("routed_to") == "rejected":
        return {"status": "error", "reason": result.get("error", "rejected")}
    return {"status": "published", "msg_id": msg_id}


__all__ = ["AUTHORITY_DECISION_EVENT", "publish_authority_decision"]
