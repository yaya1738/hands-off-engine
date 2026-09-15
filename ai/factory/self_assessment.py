from typing import Any, Dict, List, Optional

from ai.factory.interaction_health_observer import FactoryInteractionHealthObserver
from ai.factory.decision_context_observer import FactoryDecisionContextObserver


class FactorySelfAssessment:
    def __init__(
        self,
        interaction_observer: Optional[FactoryInteractionHealthObserver] = None,
        decision_context_observer: Optional[FactoryDecisionContextObserver] = None,
    ):
        self._history: List[Dict[str, Any]] = []
        self._interaction_observer = interaction_observer or FactoryInteractionHealthObserver()
        self._decision_context_observer = decision_context_observer

    def assess(self, metrics: Dict[str, Any]):
        success_rate = metrics.get("success_rate", 0)
        health = success_rate

        interaction_health = metrics.get("interaction_health")
        if interaction_health is None:
            interaction_health = self._interaction_observer.observe()

        decision_context = metrics.get("decision_context")
        if decision_context is None and self._decision_context_observer is not None:
            decision_context = self._decision_context_observer.observe()
        if not isinstance(decision_context, dict):
            decision_context = {"available": False}

        assessment_metrics = dict(metrics)
        assessment_metrics["interaction_health"] = interaction_health
        assessment_metrics["decision_context"] = decision_context

        result = {
            "health": health,
            "gaps": self.detect_gaps(assessment_metrics),
            "objective": metrics.get("objective"),
            "context": metrics.get("context", ""),
            "target": metrics.get("target", ""),
            "development_type": metrics.get("development_type", ""),
            "capability_context": metrics.get("capability_context", {}),
            "interaction_health": interaction_health,
            "decision_context": decision_context,
        }
        self._history.append(result)
        return result

    def detect_gaps(self, metrics: Dict[str, Any]):
        gaps = []
        if metrics.get("success_rate", 0) < 0.8:
            gaps.append("low success rate")
        if metrics.get("average_impact", 0) < 0.3:
            gaps.append("low improvement impact")

        interaction = metrics.get("interaction_health", {})
        if isinstance(interaction, dict) and interaction.get("available", False):
            if interaction.get("interaction_correlation_rate", 1.0) < 0.8:
                gaps.append("low interaction correlation")
            if interaction.get("interaction_orphan_replies", 0) > 0:
                gaps.append("orphaned interaction replies")
            if interaction.get("interaction_window_truncated", False):
                gaps.append("truncated interaction observation window")

        return gaps

    def recommend(self, assessment: Dict[str, Any]):
        return [f"improve {gap}" for gap in assessment.get("gaps", [])]

    def history(self):
        return self._history
