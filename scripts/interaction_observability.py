#!/usr/bin/env python3
"""Machine-readable, read-only interaction observability for Factory/agents."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scripts.control_room_state import build_snapshot


def read_interaction_health(
    repo_root: Optional[Path] = None,
    bus_limit: int = 120,
) -> Dict[str, Any]:
    """Return bounded correlation health without side effects or persistence."""
    snapshot = build_snapshot(repo_root, bus_limit=bus_limit)
    health = snapshot.get("correlation_health")
    if not isinstance(health, dict):
        return {"available": False}
    return dict(health)


__all__ = ["read_interaction_health"]
