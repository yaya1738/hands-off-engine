from ai.factory.goal_optimizer import (
    FactoryGoalOptimizer,
)


class FakeMission:
    def __init__(self):
        self.goals = [
            {
                "id": 1,
                "name": "IMPROVE",
            }
        ]


def build():
    return FactoryGoalOptimizer(
        FakeMission()
    )


def test_score_goals():
    optimizer = build()

    result = optimizer.score_goals()

    assert result["scores"][0]["score"] == 1


def test_optimize():
    optimizer = build()

    result = optimizer.optimize()

    assert result["optimized"] is True


def test_adjust():
    optimizer = build()

    result = optimizer.adjust(
        {
            "id": 1,
        }
    )

    assert result["adjusted"] is True


def test_select_best():
    optimizer = build()

    result = optimizer.select_best()

    assert result["best"]["goal"]["id"] == 1


def test_history():
    optimizer = build()

    optimizer.optimize()

    assert len(optimizer.history()) == 2
