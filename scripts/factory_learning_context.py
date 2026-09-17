#!/usr/bin/env python3
"""Project bounded learning evidence into Factory decision context.

Observation only: this adapter consumes an already-derived learning observation
and never writes learning state, authorizes work, or executes anything.
"""
from __future__ import annotations

from typing import Any, Dict


def project_factory_learning_context(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Return the minimal learning evidence suitable for Factory reasoning."""
    if not isinstance(observation, dict) or not observation.get("available", False):
        return {"available": False}

    return {
        "available": True,
        "lifecycle_entry_count": int(observation.get("lifecycle_entry_count", 0)),
        "completed_count": int(observation.get("completed_count", 0)),
        "observed_count": int(observation.get("observed_count", 0)),
        "outcome_count": int(observation.get("outcome_count", 0)),
        "success_count": int(observation.get("success_count", 0)),
        "failure_count": int(observation.get("failure_count", 0)),
        "outcome_observation_rate": observation.get("outcome_observation_rate"),
    }


__all__ = ["project_factory_learning_context"]
