import json
from pathlib import Path

from ai.factory.goal_genesis import FactoryGoalGenesis


def test_persistent_strategic_objective_is_propagated(tmp_path: Path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "strategic_objectives.json").write_text(json.dumps({
        "objectives": [{
            "id": "adaptive-human-independence",
            "priority": 1,
            "status": "persistent",
            "success_criteria": ["reduce routine intervention"],
            "operating_loop": ["observe", "act_within_authority", "verify"],
        }]
    }), encoding="utf-8")

    goal = FactoryGoalGenesis(tmp_path).generate_goal({"objective": "Improve recovery"})

    assert goal["objective"] == "Improve recovery"
    assert goal["strategic_objective_id"] == "adaptive-human-independence"
    assert goal["success_criteria"] == ["reduce routine intervention"]
    assert goal["operating_loop"] == ["observe", "act_within_authority", "verify"]


def test_missing_strategic_config_does_not_break_goal_genesis(tmp_path: Path):
    goal = FactoryGoalGenesis(tmp_path).generate_goal({"objective": "Improve recovery"})
    assert goal["objective"] == "Improve recovery"
    assert "strategic_objective_id" not in goal
