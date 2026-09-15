from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path

from scripts.interaction_observability import read_interaction_health


class FactoryInteractionHealthObserver:
    """Read-only bridge from canonical interaction health into Factory metrics."""

    def observe(
        self,
        repo_root: Optional[Path] = None,
        bus_limit: int = 120,
    ) -> Dict[str, Any]:
        health = read_interaction_health(repo_root, bus_limit=bus_limit)
        if not health.get("available", True):
            return {"available": False}

        events = int(health.get("correlated_event_count", 0))
        total = events + int(health.get("orphan_reply_count", 0)) + int(
            health.get("single_event_count", 0)
        )
        return {
            "available": True,
            "interaction_correlation_rate": (
                events / total if total else 1.0
            ),
            "interaction_orphan_replies": int(
                health.get("orphan_reply_count", 0)
            ),
            "interaction_unlinked_events": int(
                health.get("single_event_count", 0)
            ),
            "interaction_task_thread_coverage": float(
                health.get("explicit_task_thread_coverage", 0.0)
            ),
            "interaction_window_truncated": bool(
                health.get("window", {}).get("truncated", False)
            ),
            "interaction_health": health,
        }


__all__ = ["FactoryInteractionHealthObserver"]
