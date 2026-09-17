#!/usr/bin/env python3
"""Build bounded learning evidence from already-observed bus/lifecycle data."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from scripts.factory_learning_observation import build_learning_observation


def project_learning_observation(
    lifecycle_entries: Iterable[Dict[str, Any]],
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Project explicit task outcomes without rereading, inferring, or mutating state."""
    outcomes = []
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "task_result":
            continue
        context = event.get("context")
        if not isinstance(context, dict):
            continue
        status = context.get("status")
        if not isinstance(status, str):
            continue
        outcomes.append({"status": status})
    return build_learning_observation(lifecycle_entries, outcomes)


__all__ = ["project_learning_observation"]
