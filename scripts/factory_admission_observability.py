#!/usr/bin/env python3
"""Read-only Factory-facing admission observation from a shared snapshot."""
from __future__ import annotations

from typing import Any, Dict


def project_admission_observation(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return the bounded admission observation already present in the shared snapshot."""
    if not isinstance(snapshot, dict):
        return {"available": False}
    observation = snapshot.get("admission_observation")
    if not isinstance(observation, dict) or observation.get("available") is False:
        return {"available": False}
    return {
        "available": True,
        "msg_id": observation.get("msg_id"),
        "reply_to": observation.get("reply_to"),
        "task_id": observation.get("task_id"),
        "admitted": bool(observation.get("admitted", False)),
        "reason": observation.get("reason"),
        "decided_at": observation.get("decided_at"),
    }


__all__ = ["project_admission_observation"]
