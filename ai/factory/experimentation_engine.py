from typing import Any, Dict, List


class FactoryExperimentationEngine:
    def __init__(self):
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.trials: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def create_experiment(
        self,
        name: str,
        experiment: Dict[str, Any],
    ):
        self.experiments[name] = experiment

        result = {
            "created": True,
            "experiment": name,
        }

        self._history.append(result)

        return result

    def run_trial(
        self,
        experiment: str,
        trial: Dict[str, Any],
    ):
        result = {
            "run": True,
            "experiment": experiment,
            "trial": trial,
        }

        self.trials.append(result)
        self._history.append(result)

        return result

    def compare_results(
        self,
        results: List[Dict[str, Any]],
    ):
        result = {
            "compared": True,
            "count": len(results),
        }

        self._history.append(result)

        return result

    def select_winner(
        self,
        candidates: List[Dict[str, Any]],
    ):
        result = {
            "selected": True,
            "count": len(candidates),
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
