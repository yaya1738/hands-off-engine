from typing import Any, Dict, List

from ai.factory.gap_resolution_engine import (
    FactoryGapResolutionEngine,
)


class FactoryEvolutionMonitor:
    def __init__(self):
        self.gap_engine = FactoryGapResolutionEngine()
        self._history: List[Dict[str, Any]] = []

    def evaluate_state(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
    ):
        comparison = self.gap_engine.compare_target(
            current_capabilities,
            desired_capabilities,
        )

        result = {
            "needs_evolution": not comparison["complete"],
            "missing_capabilities": comparison["missing"],
        }

        self._history.append(result)

        return result

    def detect_improvement_opportunity(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        workflow_issue: str,
    ):
        gap = self.gap_engine.identify_gap(
            current_capabilities,
            desired_capabilities,
            workflow_issue,
        )

        result = {
            "opportunity_detected": gap["gap_identified"],
            "gap": gap,
        }

        self._history.append(result)

        return result

    def trigger_gap_analysis(
        self,
        component_name: str,
        purpose: str,
        responsibilities: List[str],
    ):
        return self.gap_engine.generate_component_request(
            component_name,
            purpose,
            responsibilities,
        )

    def history(self):
        return self._history
