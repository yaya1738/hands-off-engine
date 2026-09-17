#!/usr/bin/env python3
"""Build a bounded Factory learning observation from existing lifecycle data.

This is evidence only. It does not write learning state, create suggestions,
or authorize execution. The canonical coordination bus remains the source of
truth and lifecycle data remains a derived projection.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable


def build_learning_observation(
    lifecycle_entries: Iterable[Dict[str, Any]],
    outcome_observations: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Summarize explicit lifecycle/outcome signals without inference."""
    entries = [entry for entry in lifecycle_entries if isinstance(entry, dict)]
    outcomes = [item for item in outcome_observations if isinstance(item, dict)]

    if not entries and not outcomes:
        return {"available": False}

    completed = sum(
        1 for entry in entries
        if isinstance(entry.get("states"), dict) and "completed" in entry["states"]
    )
    observed = sum(
        1 for entry in entries
        if isinstance(entry.get("states"), dict) and "observed" in entry["states"]
    )
    successful = sum(1 for item in outcomes if item.get("status") == "success")
    failed = sum(1 for item in outcomes if item.get("status") in {"error", "failed", "timeout"})

    return {
        "available": True,
        "lifecycle_entry_count": len(entries),
        "completed_count": completed,
        "observed_count": observed,
        "outcome_count": len(outcomes),
        "success_count": successful,
        "failure_count": failed,
        "outcome_observation_rate": observed / completed if completed else None,
    }


__all__ = ["build_learning_observation"]
