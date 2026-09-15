#!/usr/bin/env python3
"""Machine-readable, read-only interaction observability for Factory/agents.

This adapter deliberately reuses the Control Room snapshot rather than creating
another transport or state store. The canonical coordination bus remains the
source of truth; the returned health data is only a bounded derived view.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scripts.control_room_state import build_snapshot


def read_interaction_health(
    repo_root: Optional[Path] = None,
    bus_limit: int = 120,
) -> Dict[str, Any]:
    """Return bounded correlation health for machine consumers without side effects."""
    snapshot = build_snapshot(repo_root, bus_limit=bus_limit)
    health = snapshot.get("correlation_health")
    if not isinstance(health, dict):
        return {"available": False}
    return dict(health)


__all__ = ["read_interaction_health"]
