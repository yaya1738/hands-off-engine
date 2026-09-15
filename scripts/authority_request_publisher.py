#!/usr/bin/env python3
"""Publish bounded Factory authority requests through the canonical bus."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.comm_hub import CommHub

AUTHORITY_REQUEST_EVENT = "authority_request"


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
                request = payload.get("request") if isinstance(payload, dict) else None
                if (
                    isinstance(payload, dict)
                    and payload.get("event_type") == AUTHORITY_REQUEST_EVENT
                    and isinstance(request, dict)
                    and request.get("msg_id") == msg_id
                ):
                    return True
    except OSError:
        return False
    return False


def publish_authority_request(
    request: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Publish an authority request without authorizing or executing it."""
    if not isinstance(request, dict):
        return {"status": "skipped", "reason": "invalid_request"}

    command = request.get("command")
    if not isinstance(command, dict):
        return {"status": "skipped", "reason": "missing_command"}

    correlation = command.get("correlation")
    if not isinstance(correlation, dict):
        return {"status": "skipped", "reason": "missing_correlation"}

    msg_id = correlation.get("msg_id")
    task_id = correlation.get("task_id")
    if not msg_id and not task_id:
        return {"status": "skipped", "reason": "missing_identity"}

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent.parent
    messages_file = root / "ai" / "coordination" / "messages.jsonl"
    identity = str(msg_id or task_id)

    if _already_published(messages_file, identity):
        return {"status": "already_published", "msg_id": msg_id, "task_id": task_id}

    payload = {
        "event_type": AUTHORITY_REQUEST_EVENT,
        "request": {
            "msg_id": str(msg_id) if msg_id else None,
            "reply_to": command.get("reply_to") or msg_id,
            "task_id": str(task_id) if task_id else None,
            "mode": str(command.get("mode", "DRYRUN")).upper(),
            "approval_status": "pending",
            "objective": command.get("objective"),
            "priority": command.get("priority", 0),
        },
    }

    result = CommHub(repo_root=root).receive(
        "factory",
        AUTHORITY_REQUEST_EVENT,
        payload,
        channel="messages_jsonl",
    )
    if result.get("routed_to") == "rejected":
        return {"status": "error", "reason": result.get("error", "rejected")}
    return {"status": "published", "msg_id": msg_id, "task_id": task_id}


__all__ = ["AUTHORITY_REQUEST_EVENT", "publish_authority_request"]
