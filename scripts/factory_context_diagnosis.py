#!/usr/bin/env python3
"""Classify bounded Factory decision-context observations.

Observation only: this helper diagnoses evidence quality/degradation and never
prioritizes, authorizes, routes, executes, or persists work.
"""
from __future__ import annotations

from typing import Any, Dict


def diagnose_factory_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a small fail-closed diagnosis from an existing decision context."""
    if not isinstance(context, dict):
        return {"available": False}

    interaction = context.get("interaction")
    system_health = context.get("system_health")
    if not isinstance(interaction, dict):
        interaction = {"available": False}
    if not isinstance(system_health, dict):
        system_health = {"available": False}

    if not interaction.get("available", False) or not system_health.get("available", False):
        diagnosis = "observation_incomplete"
    elif (
        interaction.get("window_truncated", False)
        or float(interaction.get("correlation_rate", 1.0)) < 0.8
        or int(interaction.get("orphan_reply_count", 0)) > 0
    ):
        diagnosis = "interaction_degradation"
    elif (
        int(system_health.get("error_count", 0)) > 0
        or system_health.get("status") not in (None, "ok", "healthy")
        or float(system_health.get("recent_error_rate", 0.0)) > 0.0
    ):
        diagnosis = "system_health_degradation"
    else:
        diagnosis = "healthy"

    return {
        "available": True,
        "diagnosis": diagnosis,
        "observation_complete": diagnosis != "observation_incomplete",
    }


__all__ = ["diagnose_factory_context"]
