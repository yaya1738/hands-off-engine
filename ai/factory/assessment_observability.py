from __future__ import annotations

from typing import Any, Dict


class FactoryAssessmentObservability:
    """Read-only projection of the latest Factory assessment for observers."""

    def snapshot(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(assessment, dict):
            return {"available": False}

        interaction = assessment.get("interaction_health", {})
        if not isinstance(interaction, dict):
            interaction = {}

        return {
            "available": True,
            "health": assessment.get("health"),
            "gaps": list(assessment.get("gaps", [])),
            "objective": assessment.get("objective"),
            "interaction_health": interaction,
        }


__all__ = ["FactoryAssessmentObservability"]
