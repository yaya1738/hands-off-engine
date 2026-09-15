#!/usr/bin/env python3
"""Read-only Factory assessment projection from the canonical coordination bus."""
from __future__ import annotations

from typing import Any, Dict, Iterable


def latest_factory_assessment(events: Iterable[dict]) -> Dict[str, Any]:
    """Return the latest explicitly published Factory assessment, fail-closed."""
    for event in reversed(list(events)):
        if not isinstance(event, dict) or event.get("type") != "factory.assessment":
            continue
        payload = event.get("payload")
        assessment = payload.get("assessment") if isinstance(payload, dict) else None
        if not isinstance(assessment, dict):
            continue
        interaction = assessment.get("interaction_health", {})
        if not isinstance(interaction, dict):
            interaction = {}
        return {
            "available": True,
            "health": assessment.get("health"),
            "gaps": list(assessment.get("gaps", [])),
            "objective": assessment.get("objective"),
            "interaction_health": interaction,
        }
    return {"available": False}


__all__ = ["latest_factory_assessment"]
