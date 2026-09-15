#!/usr/bin/env python3
"""Assess completeness of the bounded Factory decision context."""
from __future__ import annotations

from typing import Any, Dict


def summarize_context_quality(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return observation quality only; never authorize or execute work."""
    if not isinstance(context, dict):
        return {"available": False}

    interaction = context.get("interaction")
    system_health = context.get("system_health")
    if not isinstance(interaction, dict):
        interaction = {"available": False}
    if not isinstance(system_health, dict):
        system_health = {"available": False}

    gaps = []
    if not interaction.get("available", False):
        gaps.append("interaction observation unavailable")
    if not system_health.get("available", False):
        gaps.append("system health observation unavailable")
    if interaction.get("window_truncated", False):
        gaps.append("interaction observation window truncated")
    if system_health.get("error_count", 0) > 0:
        gaps.append("system health reports recent errors")

    return {
        "available": True,
        "complete": not gaps,
        "gaps": gaps,
        "interaction_available": bool(interaction.get("available", False)),
        "system_health_available": bool(system_health.get("available", False)),
    }


__all__ = ["summarize_context_quality"]
