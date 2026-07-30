from typing import Any, Dict, List
from pathlib import Path
import json


class FactoryDecisionIntelligence:
    def __init__(self):
        self.decisions: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
        self.history_file = Path("state/factory_decision_history.jsonl")
        self.history_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.history_file.exists():
            for line in self.history_file.read_text().splitlines():
                try:
                    self._history.append(json.loads(line))
                except Exception:
                    pass

    def create_decision(
        self,
        decision: Dict[str, Any],
    ):
        self.decisions.append(decision)

        result = {
            "created": True,
            "decision": decision,
        }

        self._history.append(result)

        with self.history_file.open("a") as f:
            f.write(
                json.dumps(self._json_safe(result))
                + "\n"
            )

        return result

    def evaluate_options(
        self,
        options: List[Dict[str, Any]],
    ):
        result = {
            "evaluated": True,
            "count": len(options),
        }

        self._history.append(result)

        return result

    def score_decision(
        self,
        decision: Dict[str, Any],
    ):
        result = {
            "scored": True,
            "decision": decision,
        }

        self._history.append(result)

        return result

    def select_action(
        self,
        options,
    ):
        if not options:
            return {
                "selected": True,
                "action": None,
            }

        return {
            "selected": True,
            "action": options[0],
        }



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
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
    ):
        result = {
            "decision": decision,
            "outcome": outcome,
            "learned": True,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
