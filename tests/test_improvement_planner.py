from ai.factory.improvement_planner import (
    FactoryImprovementPlanner,
)


def test_plan():
    planner = FactoryImprovementPlanner()

    result = planner.plan(
        {
            "health": 0.6,
            "gaps": [
                "slow recovery",
            ],
        }
    )

    assert "address slow recovery" in (
        result["tasks"]
    )


def test_priority():
    planner = FactoryImprovementPlanner()

    result = planner.prioritize(
        {
            "health": 0.8,
        }
    )

    assert result == 0.2


def test_history():
    planner = FactoryImprovementPlanner()

    planner.plan(
        {
            "health": 1,
            "gaps": [],
        }
    )

    assert len(planner.history()) == 1
