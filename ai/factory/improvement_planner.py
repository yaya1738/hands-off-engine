from typing import Any, Dict, List


class FactoryImprovementPlanner:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def plan(
        self,
        assessment: Dict[str, Any],
    ):
        gaps = assessment.get(
            "gaps",
            [],
        )

        tasks = [
            f"address {gap}"
            for gap in gaps
        ]

        decision_context = assessment.get("decision_context")
        if not isinstance(decision_context, dict):
            decision_context = {"available": False}

        result = {
            "goal": assessment.get(
                "objective",
                "improve factory performance",
            ),
            "tasks": tasks,
            "priority": self.prioritize(
                assessment
            ),
            "context": assessment.get(
                "context",
                "",
            ),
            "target": assessment.get(
                "target",
                "",
            ),
            "development_type": assessment.get(
                "development_type",
                "",
            ),
            "capability_context": assessment.get(
                "capability_context",
                {},
            ),
            "components": assessment.get(
                "components",
                [],
            ),
            "integration_points": assessment.get(
                "integration_points",
                [],
            ),
            "validation": assessment.get(
                "validation",
                [],
            ),
            "rollback": assessment.get(
                "rollback",
                [],
            ),
            "decision_context": dict(decision_context),
        }

        self._history.append(
            result
        )

        return result

    def prioritize(
        self,
        assessment: Dict[str, Any],
    ):
        health = assessment.get(
            "health",
            1,
        )
        priority = 1 - health

        decision_context = assessment.get("decision_context")
        if not isinstance(decision_context, dict):
            decision_context = {"available": False}

        interaction = decision_context.get("interaction")
        if isinstance(interaction, dict) and decision_context.get("available", False):
            correlation_rate = float(interaction.get("correlation_rate", 1.0))
            orphan_replies = int(interaction.get("orphan_reply_count", 0))
            if correlation_rate < 0.8 or orphan_replies > 0:
                priority = max(priority, 0.8)

        return round(priority, 2)

    def history(self):
        return self._history
