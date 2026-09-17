#!/usr/bin/env python3
"""Project bounded outcome evidence from the existing lifecycle projection.

Lifecycle state is derived from the canonical coordination bus. This helper
only exposes an observation for Factory reasoning and never mutates state.
"""
from __future__ import annotations

from typing import Any, Dict


def project_factory_outcome(lifecycle: Dict[str, Any]) -> Dict[str, Any]:
    """Return explicit lifecycle outcome evidence, failing closed."""
    if not isinstance(lifecycle, dict):
        return {"available": False}

    states = lifecycle.get("states")
    if not isinstance(states, dict):
        states = {}

    completed = "completed" in states
    result_published = "result_published" in states
    observed = "observed" in states

    return {
        "available": bool(lifecycle.get("task_id")),
        "task_id": lifecycle.get("task_id"),
        "msg_id": lifecycle.get("msg_id"),
        "reply_to": lifecycle.get("reply_to"),
        "status": lifecycle.get("status"),
        "completed": completed,
        "result_published": result_published,
        "observed": observed,
        "updated_at": lifecycle.get("updated_at"),
    }


__all__ = ["project_factory_outcome"]
