from ai.factory.goal_management import (
    FactoryGoalManagement,
)


def build():
    return FactoryGoalManagement()


def test_create_goal():
    manager = build()

    result = manager.create_goal(
        {
            "goal": "IMPROVE",
        }
    )

    assert result["created"] is True


def test_prioritize_goals():
    manager = build()

    manager.create_goal(
        {
            "id": 1,
        }
    )

    result = manager.prioritize_goals()

    assert result["priority_goal"]["id"] == 1


def test_track_progress():
    manager = build()

    result = manager.track_progress(
        {},
        50,
    )

    assert result["tracked"] is True


def test_complete_goal():
    manager = build()

    result = manager.complete_goal(
        {}
    )

    assert result["completed"] is True


def test_history():
    manager = build()

    manager.create_goal({})

    assert len(manager.history()) == 1
