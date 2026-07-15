from typing import Any, Dict, List


class FactoryExperimentationIntelligence:
    def __init__(self):
        self.experiments: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_experiment(
        self,
        experiment: Dict[str, Any],
    ):
        self.experiments.append(experiment)

        result = {
            "created": True,
            "experiment": experiment,
        }

        self._history.append(result)

        return result

    def run_experiment(
        self,
        experiment: Dict[str, Any],
    ):
        result = {
            "run": True,
            "experiment": experiment,
        }

        self.results.append(result)
        self._history.append(result)

        return result

    def evaluate_experiment(
        self,
        result: Dict[str, Any],
    ):
        evaluation = {
            "evaluated": True,
            "result": result,
        }

        self._history.append(evaluation)

        return evaluation

    def promote_result(
        self,
        result: Dict[str, Any],
    ):
        promotion = {
            "promoted": True,
            "result": result,
        }

        self._history.append(promotion)

        return promotion

    def history(self):
        return self._history
