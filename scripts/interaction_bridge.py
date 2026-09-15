#!/usr/bin/env python3
"""Governed bidirectional interaction adapter.

This is a thin adapter over the existing CommHub and canonical coordination
bus. It does not execute work, create a second transport, or bypass admission.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def send_operator_message(repo_root: Path, message: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
    """Submit one operator message through the existing governed boundary."""
    text = str(message).strip()
    if not text or len(text) > 4000:
        raise ValueError("message must be 1-4000 characters")

    from scripts.comm_hub import CommHub

    payload: Dict[str, Any] = {
        "message": text,
        "source": "interaction_bridge",
    }
    if reply_to:
        payload["reply_to"] = reply_to

    result = CommHub(repo_root=Path(repo_root)).receive(
        "operator",
        "inbound_from_operator",
        payload,
        channel="interaction_bridge",
    )
    return {
        "status": "sent",
        "result": result,
        "transport": "ai/coordination/messages.jsonl",
        "governance": "CommHub.receive",
    }


def correlate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract stable correlation fields from a canonical bus event."""
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    return {
        "msg_id": event.get("id") or event.get("msg_id"),
        "task_id": context.get("task_id") or payload.get("task_id") or event.get("task_id"),
        "reply_to": payload.get("reply_to") or event.get("reply_to"),
        "type": event.get("type"),
        "timestamp": event.get("timestamp"),
    }
