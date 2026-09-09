from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Set


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

    @staticmethod
    def _bounded_number(value: Any, default: float = 0.5) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default

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
                item = {
                    "objective": objective,
                    "source": "capability_gap",
                    "score": 90,
                    "reason": "observed capability gap",
                }
                if isinstance(gap, dict):
                    for key in ("expected_value", "confidence", "reversibility", "cost", "risk"):
                        if key in gap:
                            item[key] = gap[key]
                candidates.append(item)

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
                item = {
                    "objective": objective,
                    "source": "runtime_finding",
                    "score": 80,
                    "reason": "runtime finding requires follow-up",
                }
                if isinstance(finding, dict):
                    for key in ("expected_value", "confidence", "reversibility", "cost", "risk"):
                        if key in finding:
                            item[key] = finding[key]
                candidates.append(item)

        return candidates

    def _phase_score(self, candidate: Dict[str, Any], phase: str | None, has_actionable: bool) -> float:
        """Score work according to the current operating phase."""
        source = candidate.get("source")
        base = float(candidate.get("score", 0) or 0)

        if phase == "pre_dass":
            source_bonus = {
                "integration_health": 20,
                "capability_gap": 15,
                "runtime_finding": 10,
                "autonomous_continuity": 5,
                "strategic_objective": -30 if has_actionable else 0,
            }.get(source, 0)
            return base + source_bonus

        if phase == "post_dass":
            source_bonus = {
                "integration_health": 15,
                "capability_gap": 10,
                "runtime_finding": 5,
                "autonomous_continuity": 0,
                "strategic_objective": -35 if has_actionable else 0,
            }.get(source, 0)
            value = self._bounded_number(candidate.get("expected_value"))
            confidence = self._bounded_number(candidate.get("confidence"))
            reversibility = self._bounded_number(candidate.get("reversibility"))
            cost = self._bounded_number(candidate.get("cost"), 0.5)
            risk = self._bounded_number(candidate.get("risk"), 0.0)
            return base + source_bonus + 15 * value + 8 * confidence + 5 * reversibility - 8 * cost - 12 * risk

        return base

    def prioritize(
        self,
        candidates: Iterable[Dict[str, Any]],
        excluded_objectives: Iterable[str] | None = None,
        cycle_count: int = 0,
        phase: str | None = None,
    ) -> Dict[str, Any] | None:
        excluded: Set[str] = {
            self._text(objective).casefold()
            for objective in (excluded_objectives or [])
            if self._text(objective)
        }
        candidate_list = list(candidates)
        has_actionable = any(
            candidate.get("source") in {"capability_gap", "integration_health", "runtime_finding"}
            for candidate in candidate_list
            if isinstance(candidate, dict)
        )
        normalized: Dict[str, Dict[str, Any]] = {}
        for candidate in candidate_list:
            objective = self._text(candidate.get("objective"))
            if not objective or objective.casefold() in excluded:
                continue
            key = objective.casefold()
            item = {**candidate, "objective": objective}
            item["priority_score"] = self._phase_score(item, phase, has_actionable)
            current = normalized.get(key)
            if current is None or item["priority_score"] > current.get("priority_score", float("-inf")):
                normalized[key] = item

        if not normalized:
            strategic = next(
                (
                    self._text(candidate.get("objective"))
                    for candidate in candidate_list
                    if self._text(candidate.get("objective"))
                    and candidate.get("source") == "strategic_objective"
                ),
                "",
            )
            if strategic and strategic.casefold() in excluded:
                cycle = max(1, int(cycle_count or 0))
                while True:
                    continuity = (
                        f"Perform bounded autonomous continuity checkpoint {cycle}: "
                        "inspect the governed runtime for the highest-value actionable "
                        "capability gap, validate the finding through existing safety "
                        "and authority gates, and record the next bounded improvement "
                        "without weakening any safety, audit, cost, risk, or verification boundary."
                    )
                    if continuity.casefold() not in excluded:
                        break
                    cycle += 1
                normalized[continuity.casefold()] = {
                    "objective": continuity,
                    "source": "autonomous_continuity",
                    "score": 94,
                    "priority_score": self._phase_score(
                        {"source": "autonomous_continuity", "score": 94}, phase, has_actionable
                    ),
                    "reason": "bounded continuity objective after candidate exhaustion",
                    "strategic_objective": strategic,
                }

        if not normalized:
            return None

        ranked = sorted(
            normalized.values(),
            key=lambda item: (-float(item.get("priority_score", item.get("score", 0))), item["objective"].casefold()),
        )
        selected = dict(ranked[0])
        selected["strategic_objective_id"] = self.STRATEGIC_OBJECTIVE_ID
        selected["authority"] = "FactoryAuthorityGateway"
        selected["execution_permitted"] = False
        selected["selected_at"] = datetime.now(timezone.utc).isoformat()
        return selected

    def select_next(self, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        candidates = self.discover_candidates(context)
        selected = self.prioritize(
            candidates,
            context.get("excluded_objectives", []),
            int(context.get("cycle_count", 0) or 0),
            context.get("phase"),
        )
        result = {
            "status": "selected" if selected else "no_candidate",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "excluded_objectives": list(context.get("excluded_objectives", [])),
            "phase": context.get("phase"),
            "selected": selected,
        }
        self._history.append(result)
        return result

    def history(self) -> List[Dict[str, Any]]:
        return self._history
