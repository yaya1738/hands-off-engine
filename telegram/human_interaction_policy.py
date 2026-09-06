#!/usr/bin/env python3
"""Adaptive policy for deciding when human interaction adds material value.

This policy optimizes for fewer routine interruptions and richer, more useful
interactions. It never grants execution authority and cannot override safety,
approval, credential, or fail-closed controls.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class HumanInteractionPolicy:
    """Classify whether an event warrants contacting the human."""

    ALWAYS_ESCALATE = {"critical", "decision"}

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "state" / "communication" / "interaction_metrics.json"

    def should_notify(
        self,
        *,
        kind: str,
        priority: str,
        requires_response: bool = False,
        routine: bool = False,
        autonomous_resolution: bool = False,
    ) -> bool:
        """Return True only when communication has material human value."""
        if kind in self.ALWAYS_ESCALATE:
            return True
        if kind == "blocker":
            return priority in {"high", "critical"} or requires_response
        if requires_response:
            return True
        if kind == "progress":
            return not routine
        if autonomous_resolution:
            return False
        return priority in {"high", "critical"}

    def record_outcome(
        self,
        *,
        contacted: bool,
        human_response: bool = False,
        autonomous_resolution: bool = False,
        materially_changed: bool = False,
    ) -> dict[str, Any]:
        """Record interaction value for future policy evaluation.

        Metrics are evidence only. They do not mutate authority or permissions.
        """
        metrics = self._load()
        metrics["events"] += 1
        metrics["contacts"] += int(contacted)
        metrics["human_responses"] += int(human_response)
        metrics["autonomous_resolutions"] += int(autonomous_resolution)
        metrics["material_human_impact"] += int(materially_changed)
        metrics["updated_at"] = time.time()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return metrics

    def summary(self) -> dict[str, Any]:
        metrics = self._load()
        events = metrics["events"]
        return {
            **metrics,
            "contact_rate": (metrics["contacts"] / events) if events else 0.0,
            "human_value_rate": (metrics["material_human_impact"] / metrics["human_responses"])
            if metrics["human_responses"] else 0.0,
        }

    def _load(self) -> dict[str, Any]:
        defaults = {
            "events": 0,
            "contacts": 0,
            "human_responses": 0,
            "autonomous_resolutions": 0,
            "material_human_impact": 0,
            "updated_at": None,
        }
        if not self.path.exists():
            return defaults
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            defaults.update({key: loaded[key] for key in defaults if key in loaded})
        except (OSError, json.JSONDecodeError, TypeError):
            return defaults
        return defaults
