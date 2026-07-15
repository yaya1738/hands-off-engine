from ai.factory.mission_controller import (
    FactoryMissionController,
)


def build():
    return FactoryMissionController()


def test_set_goal():
    controller = build()

    result = controller.set_goal(
        {
            "objective": "IMPROVE",
        }
    )

    assert result["goal_set"] is True


def test_progress():
    controller = build()

    controller.set_goal({})

    result = controller.evaluate_progress()

    assert result["progress"] == "TRACKING"


def test_prioritize():
    controller = build()

    controller.set_goal(
        {
            "id": 1,
        }
    )

    result = controller.prioritize()

    assert result["priority"]["id"] == 1


def test_advance():
    controller = build()

    result = controller.advance()

    assert result["advanced"] is True


def test_history():
    controller = build()

    controller.advance()

    assert len(controller.history()) == 1
