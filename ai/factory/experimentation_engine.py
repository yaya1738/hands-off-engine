from typing import Any, Dict, List


class FactoryExperimentationEngine:
    def __init__(self):
        self.experiments: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_experiment(
        self,
        experiment: Dict[str, Any],
    ):
        self.experiments.append(
            experiment
        )

        result = {
            "created": True,
            "experiment": experiment,
        }

        self._history.append(
            result
        )

        return result

    def run_experiment(
        self,
        experiment: Dict[str, Any],
    ):
        result = {
            "run": True,
            "experiment": experiment,
            "outcome": "COMPLETE",
        }

        self.results.append(
            result
        )

        self._history.append(
            result
        )

        return result

    def measure_result(
        self,
        result: Dict[str, Any],
    ):
        measured = {
            "measured": True,
            "result": result,
        }

        self._history.append(
            measured
        )

        return measured

    def select_winner(
        self,
        candidates: List[Dict[str, Any]],
    ):
        winner = (
            candidates[0]
            if candidates
            else None
        )

        result = {
            "winner": winner,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
