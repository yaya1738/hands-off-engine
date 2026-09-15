#!/usr/bin/env python3
"""Factory-facing read-only interaction-health projection.

The canonical coordination bus remains the only transport/source of truth.
This module converts the bounded interaction-health projection into metrics
that the existing Factory self-assessment contract can consume. It does not
route, authorize, execute, or persist state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scripts.interaction_observability import read_interaction_health


def read_factory_interaction_metrics(
    repo_root: Optional[Path] = None,
    bus_limit: int = 120,
) -> Dict[str, Any]:
    """Return bounded interaction metrics suitable for Factory assessment."""
    health = read_interaction_health(repo_root, bus_limit=bus_limit)
    if not health.get("available", False):
        return {"available": False}

    event_count = int(health.get("event_count", 0))
    correlated = int(health.get("correlated_event_count", 0))
    coverage = float(health.get("explicit_task_thread_coverage", 0.0))

    return {
        "available": True,
        "interaction_health": health,
        "interaction_event_count": event_count,
        "interaction_correlated_event_count": correlated,
        "interaction_correlation_rate": (
            correlated / event_count if event_count else 1.0
        ),
        "interaction_orphan_reply_count": int(
            health.get("orphan_reply_count", 0)
        ),
        "interaction_single_event_count": int(
            health.get("single_event_count", 0)
        ),
        "interaction_task_thread_coverage": coverage,
        "interaction_window_truncated": bool(
            health.get("window", {}).get("truncated", False)
        ),
    }


__all__ = ["read_factory_interaction_metrics"]
