from __future__ import annotations

from typing import Any, Dict, Optional


class FactoryAssessmentBusPublisher:
    """Publish the already-produced Factory assessment onto the canonical bus."""

    def __init__(self, hub=None):
        self._hub = hub

    def publish(self, assessment: Dict[str, Any]):
        if not isinstance(assessment, dict):
            return {"status": "skipped", "reason": "assessment_unavailable"}

        interaction = assessment.get("interaction_health", {})
        if not isinstance(interaction, dict):
            interaction = {}

        payload = {
            "assessment": {
                "health": assessment.get("health"),
                "gaps": list(assessment.get("gaps", [])),
                "objective": assessment.get("objective"),
                "interaction_health": interaction,
            }
        }

        hub = self._hub
        if hub is None:
            from scripts.comm_hub import CommHub
            hub = CommHub()

        return hub.send(
            "system_internal",
            "factory.assessment",
            payload,
            source="factory",
        )


__all__ = ["FactoryAssessmentBusPublisher"]
