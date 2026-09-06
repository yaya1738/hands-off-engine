from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class FactoryGoalGenesis:
    """Generate candidate goals with durable strategic context.

    Strategic objectives provide context and success criteria; they do not grant
    execution authority or override explicit recommendation objectives.
    """

    def __init__(self, repo_root: Path | None = None):
        self._history: List[Dict[str, Any]] = []
        self._repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
        self._strategic_objectives = self._load_strategic_objectives()

    def _load_strategic_objectives(self) -> List[Dict[str, Any]]:
        path = self._repo_root / "config" / "strategic_objectives.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return []
        objectives = data.get("objectives", [])
        return objectives if isinstance(objectives, list) else []

    def _primary_strategic_objective(self) -> Dict[str, Any] | None:
        active = [
            item for item in self._strategic_objectives
            if isinstance(item, dict) and item.get("status") == "persistent"
        ]
        if not active:
            return None
        return min(active, key=lambda item: item.get("priority", 999999))

    def generate_goal(self, recommendation: Dict[str, Any]):
        strategic = self._primary_strategic_objective()
        goal = {
            "objective": recommendation.get(
                "objective",
                "Improve runtime performance",
            ),
            "priority": 2,
            "source": "self_improvement",
            "status": "candidate",
        }
        if strategic:
            goal["strategic_objective_id"] = strategic.get("id")
            goal["success_criteria"] = list(strategic.get("success_criteria", []))
            goal["operating_loop"] = list(strategic.get("operating_loop", []))

        self._history.append(goal)
        return goal

    def history(self):
        return self._history
