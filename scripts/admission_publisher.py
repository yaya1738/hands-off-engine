#!/usr/bin/env python3
"""Publish bounded Factory admission decisions through the canonical bus."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.comm_hub import CommHub

ADMISSION_EVENT = "task_admission"


def _already_published(messages_file: Path, msg_id: str) -> bool:
    if not messages_file.exists():
        return False
    try:
        with messages_file.open("r") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = event.get("payload")
                decision = payload.get("decision") if isinstance(payload, dict) else None
                if (
                    isinstance(payload, dict)
                    and payload.get("event_type") == ADMISSION_EVENT
                    and isinstance(decision, dict)
                    and decision.get("msg_id") == msg_id
                ):
                    return True
    except OSError:
        return False
    return False


def publish_admission_decision(
    decision: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Publish an explicit admission observation, without admission side effects."""
    if not isinstance(decision, dict) or not decision.get("msg_id"):
        return {"status": "skipped", "reason": "invalid_decision"}

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent.parent
    messages_file = root / "ai" / "coordination" / "messages.jsonl"
    msg_id = str(decision["msg_id"])

    if _already_published(messages_file, msg_id):
        return {"status": "already_published", "msg_id": msg_id}

    context = decision.get("context")
    context = context if isinstance(context, dict) else {}
    payload = {
        "event_type": ADMISSION_EVENT,
        "decision": {
            "msg_id": msg_id,
            "reply_to": decision.get("reply_to", msg_id),
            "task_id": decision.get("task_id") or context.get("task_id"),
            "admitted": bool(decision.get("admitted", False)),
            "reason": decision.get("reason"),
            "decided_at": decision.get("decided_at"),
        },
    }

    result = CommHub(repo_root=root).receive(
        "factory",
        ADMISSION_EVENT,
        payload,
        channel="messages_jsonl",
    )
    if result.get("routed_to") == "rejected":
        return {"status": "error", "reason": result.get("error", "rejected")}
    return {"status": "published", "msg_id": msg_id}


__all__ = ["ADMISSION_EVENT", "publish_admission_decision"]
