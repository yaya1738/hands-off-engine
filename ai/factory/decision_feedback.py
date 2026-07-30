from typing import Any, Dict, List
from pathlib import Path
import json


class FactoryDecisionFeedback:
    def __init__(self):
        self._decisions: List[Dict[str, Any]] = []
        self.state_path = Path(
            "state/factory_decision_history.jsonl"
        )
        self._load_history()

    def _load_history(self):
        if not self.state_path.exists():
            return

        for line in self.state_path.read_text().splitlines():
            if line.strip():
                self._decisions.append(
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

    def record_decision(
        self,
        decision: Dict[str, Any],
    ):
        entry = {
            "decision": decision,
            "outcome": None,
        }

        self._decisions.append(
            entry
        )

        self._persist(entry)

        return entry

    def record_outcome(
        self,
        entry: Dict[str, Any],
        outcome: Dict[str, Any],
    ):
        entry["outcome"] = outcome

        return entry

    def evaluate(
        self,
        entry: Dict[str, Any],
    ):
        outcome = entry.get(
            "outcome"
        )

        if not outcome:
            return {
                "status": "UNKNOWN",
            }

        success = outcome.get(
            "success",
            False,
        )

        return {
            "status": (
                "IMPROVED"
                if success
                else "FAILED"
            ),
            "impact": outcome.get(
                "impact",
                0,
            ),
        }

    def history(self):
        return self._decisions
