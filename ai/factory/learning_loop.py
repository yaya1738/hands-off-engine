from typing import Any, Dict, List
from pathlib import Path
import json


class FactoryLearningLoop:
    def __init__(self):
        self.outcomes: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self.state_path = Path(
            "state/factory_learning_history.jsonl"
        )
        self._load_history()

    def _load_history(self):
        if not self.state_path.exists():
            return

        for line in self.state_path.read_text().splitlines():
            if line.strip():
                self._history.append(
                    json.loads(line)
                )

    def _persist(self, entry):
        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.state_path.open("a") as f:
            f.write(
                json.dumps(entry)
                + "\n"
            )


    def _json_safe(self, value):
        if isinstance(value, dict):
            return {
                k: self._json_safe(v)
                for k, v in value.items()
            }

        if isinstance(value, list):
            return [
                self._json_safe(v)
                for v in value
            ]

        if callable(value):
            return str(value)

        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    def record_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        outcome = self._json_safe(outcome)

        self.outcomes.append(
            outcome
        )

        result = {
            "recorded": True,
            "outcome": outcome,
        }

        self._history.append(result)
        self._persist(result)

        return result

    def analyze_feedback(
        self,
        feedback: Dict[str, Any],
    ):
        result = {
            "analyzed": True,
            "feedback": feedback,
        }

        self._history.append(result)

        return result

    def update_model(
        self,
        update: Dict[str, Any],
    ):
        result = {
            "updated": True,
            "model_update": update,
        }

        self._history.append(result)

        return result

    def generate_improvement(
        self,
        idea: Dict[str, Any],
    ):
        self.improvements.append(
            idea
        )

        result = {
            "generated": True,
            "improvement": idea,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
