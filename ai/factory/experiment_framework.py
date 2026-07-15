from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


class FactoryExperimentFramework:
    def __init__(self):
        self._experiments: List[Dict[str, Any]] = []

    def create_experiment(
        self,
        name: str,
        action: Callable,
    ):
        experiment = {
            "name": name,
            "action": action,
            "status": "CREATED",
        }

        self._experiments.append(
            experiment
        )

        return experiment

    def run(
        self,
        experiment: Dict[str, Any],
    ):
        try:
            result = experiment["action"]()

            experiment["status"] = "COMPLETED"
            experiment["result"] = result

        except Exception as exc:
            experiment["status"] = "FAILED"
            experiment["error"] = str(exc)

        experiment["timestamp"] = datetime.now(
            timezone.utc
        ).isoformat()

        return experiment

    def evaluate(
        self,
        experiment: Dict[str, Any],
    ):
        if experiment.get("status") == "COMPLETED":
            return {
                "decision": "PROMOTE",
                "experiment": experiment["name"],
            }

        return {
            "decision": "REJECT",
            "experiment": experiment["name"],
        }

    def history(self):
        return self._experiments
