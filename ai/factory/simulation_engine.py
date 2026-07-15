from typing import Any, Dict, List


class FactorySimulationEngine:
    def __init__(self):
        self.scenarios: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_scenario(
        self,
        scenario: Dict[str, Any],
    ):
        self.scenarios.append(
            scenario
        )

        result = {
            "created": True,
            "scenario": scenario,
        }

        self._history.append(
            result
        )

        return result

    def simulate_action(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "simulated": True,
            "action": action,
            "outcome": "SAFE",
        }

        self.results.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def evaluate_result(
        self,
        result: Dict[str, Any],
    ):
        evaluation = {
            "evaluated": True,
            "result": result,
        }

        self._history.append(
            evaluation
        )

        return evaluation

    def compare_outcomes(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ):
        comparison = {
            "compared": True,
            "first": first,
            "second": second,
        }

        self._history.append(
            comparison
        )

        return comparison

    def history(self):
        return self._history
