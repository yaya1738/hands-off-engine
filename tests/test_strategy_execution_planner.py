from ai.factory.strategy_execution_planner import (
    FactoryStrategyExecutionPlanner,
)


def build():
    return FactoryStrategyExecutionPlanner()


def test_create_plan():
    planner = build()

    result = planner.create_plan(
        {
            "strategy": "A",
        }
    )

    assert result["plan_created"] is True


def test_decompose():
    planner = build()

    result = planner.decompose(
        {
            "task": "RUN",
        }
    )

    assert len(result["tasks"]) == 1


def test_prioritize_tasks():
    planner = build()

    result = planner.prioritize_tasks(
        [
            {
                "id": 1,
            }
        ]
    )

    assert result["priority_task"]["id"] == 1


def test_validate_plan():
    planner = build()

    result = planner.validate_plan(
        {}
    )

    assert result["valid"] is True


def test_history():
    planner = build()

    planner.create_plan({})

    assert len(planner.history()) == 1
