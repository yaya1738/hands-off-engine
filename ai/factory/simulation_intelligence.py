from typing import Any, Dict, List


class FactorySimulationIntelligence:
    def __init__(self):
        self.scenarios: List[Dict[str, Any]] = []
        self.simulations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_scenario(
        self,
        scenario: Dict[str, Any],
    ):
        self.scenarios.append(scenario)

        result = {
            "created": True,
            "scenario": scenario,
        }

        self._history.append(result)

        return result

    def run_simulation(
        self,
        scenario: Dict[str, Any],
    ):
        result = {
            "simulated": True,
            "scenario": scenario,
        }

        self.simulations.append(result)
        self._history.append(result)

        return result

    def compare_outcomes(
        self,
        outcomes: List[Dict[str, Any]],
    ):
        result = {
            "compared": True,
            "count": len(outcomes),
        }

        self._history.append(result)

        return result

    def select_scenario(
        self,
        scenarios: List[Dict[str, Any]],
    ):
        result = {
            "selected": True,
            "count": len(scenarios),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
