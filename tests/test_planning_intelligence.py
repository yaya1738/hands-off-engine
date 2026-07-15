from ai.factory.planning_intelligence import (
    FactoryPlanningIntelligence,
)


def build():
    return FactoryPlanningIntelligence()


def test_create_plan():
    planner = build()

    result = planner.create_plan(
        {
            "goal": "BUILD",
        }
    )

    assert result["created"] is True


def test_prioritize_tasks():
    planner = build()

    result = planner.prioritize_tasks(
        [
            {
                "task": 1,
            }
        ]
    )

    assert result["prioritized"] is True


def test_schedule_tasks():
    planner = build()

    result = planner.schedule_tasks(
        []
    )

    assert result["scheduled"] is True


def test_validate_plan():
    planner = build()

    result = planner.validate_plan(
        {}
    )

    assert result["validated"] is True


def test_history():
    planner = build()

    planner.create_plan({})

    assert len(planner.history()) == 1
