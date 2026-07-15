from ai.factory.goal_manager import FactoryGoalManager


def build():
    return FactoryGoalManager()


def test_register():
    engine = build()

    result = engine.register_goal(
        "primary",
        {},
    )

    assert result["registered"] is True


def test_prioritize():
    engine = build()

    result = engine.prioritize_goals()

    assert result["prioritized"] is True


def test_progress():
    engine = build()

    result = engine.evaluate_progress(
        "primary",
        {},
    )

    assert result["evaluated"] is True


def test_complete():
    engine = build()

    result = engine.complete_goal(
        "primary",
    )

    assert result["completed"] is True


def test_revise():
    engine = build()

    result = engine.revise_goal(
        "primary",
        {},
    )

    assert result["revised"] is True


def test_history():
    engine = build()

    engine.prioritize_goals()

    assert len(engine.history()) == 1
