from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


class FactoryAutonomousObjectiveLoop:
    """Select the next bounded objective without requiring a chat turn.

    This component owns discovery and prioritization only. It never grants
    execution authority and never executes an objective. Execution must still
    enter the existing FactoryAuthorityGateway and its approval/safety gates.
    """

    STRATEGIC_OBJECTIVE_ID = "adaptive-human-independence"

    def __init__(self, runtime=None):
        self.runtime = runtime
        self._history: List[Dict[str, Any]] = []

    @staticmethod
    def _text(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("objective") or value.get("name") or "").strip()
        return str(value or "").strip()

    def discover_candidates(self, context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        context = context or {}
        candidates: List[Dict[str, Any]] = []

        strategic = context.get("strategic_objective")
        if strategic:
            objective = self._text(strategic)
            if objective:
                candidates.append({
                    "objective": objective,
                    "source": "strategic_objective",
                    "score": 100,
                    "reason": "persistent strategic objective",
                })

        for gap in context.get("gaps", []):
            objective = self._text(gap)
            if objective:
                candidates.append({
                    "objective": objective,
                    "source": "capability_gap",
                    "score": 90,
                    "reason": "observed capability gap",
                })

        discovery = context.get("discovery", {})
        if isinstance(discovery, dict) and discovery.get("missing"):
            for missing in discovery["missing"]:
                objective = f"Restore autonomous integration boundary: {missing}"
                candidates.append({
                    "objective": objective,
                    "source": "integration_health",
                    "score": 95,
                    "reason": "required autonomous component is missing",
                })

        for finding in context.get("findings", []):
            objective = self._text(finding)
            if objective:
                candidates.append({
                    "objective": objective,
                    "source": "runtime_finding",
                    "score": 80,
                    "reason": "runtime finding requires follow-up",
                })

        return candidates

    def prioritize(self, candidates: Iterable[Dict[str, Any]]) -> Dict[str, Any] | None:
        normalized: Dict[str, Dict[str, Any]] = {}
        for candidate in candidates:
            objective = self._text(candidate.get("objective"))
            if not objective:
                continue
            key = objective.casefold()
            current = normalized.get(key)
            item = {**candidate, "objective": objective}
            if current is None or item.get("score", 0) > current.get("score", 0):
                normalized[key] = item

        if not normalized:
            return None

        # Stable tie-breaking keeps autonomous runs reproducible.
        ranked = sorted(
            normalized.values(),
            key=lambda item: (-int(item.get("score", 0)), item["objective"].casefold()),
        )
        selected = dict(ranked[0])
        selected["strategic_objective_id"] = self.STRATEGIC_OBJECTIVE_ID
        selected["authority"] = "FactoryAuthorityGateway"
        selected["execution_permitted"] = False
        selected["selected_at"] = datetime.now(timezone.utc).isoformat()
        return selected

    def select_next(self, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        candidates = self.discover_candidates(context)
        selected = self.prioritize(candidates)
        result = {
            "status": "selected" if selected else "no_candidate",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "selected": selected,
        }
        self._history.append(result)
        return result

    def history(self) -> List[Dict[str, Any]]:
        return self._history
