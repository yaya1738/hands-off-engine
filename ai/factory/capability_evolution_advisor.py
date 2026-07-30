from typing import Any, Dict, List

from ai.factory.evolution_monitor import (
    FactoryEvolutionMonitor,
)

from ai.factory.gap_resolution_engine import (
    FactoryGapResolutionEngine,
)


class FactoryCapabilityEvolutionAdvisor:
    def __init__(self):
        self.evolution_monitor = FactoryEvolutionMonitor()
        self.gap_engine = FactoryGapResolutionEngine()
        self._history: List[Dict[str, Any]] = []

    def evaluate_capabilities(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
    ):
        result = self.evolution_monitor.evaluate_state(
            current_capabilities,
            desired_capabilities,
        )

        self._history.append(result)

        return result

    def identify_missing_capability(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        issue: str,
    ):
        gap = self.gap_engine.identify_gap(
            current_capabilities,
            desired_capabilities,
            issue,
        )

        result = {
            "recommendation_needed": gap["gap_identified"],
            "gap": gap,
        }

        self._history.append(result)

        return result

    def generate_recommendation(
        self,
        capability_name: str,
        reason: str,
        responsibilities: List[str],
    ):
        recommendation = {
            "capability": capability_name,
            "reason": reason,
            "responsibilities": responsibilities,
            "status": "RECOMMENDED",
        }

        self._history.append(recommendation)

        return {
            "generated": True,
            "recommendation": recommendation,
        }

    def history(self):
        return self._history
