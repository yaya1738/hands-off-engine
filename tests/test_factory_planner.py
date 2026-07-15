from ai.factory.planner import FactoryPlanner


def test_planner_creates_steps():
    planner = FactoryPlanner()

    steps = planner.plan(
        {
            "goal": "build audit pipeline",
        }
    )

    assert len(steps) == 4
    assert steps[0].startswith("analyze")
    assert steps[-1].startswith("review")


def test_empty_goal():
    planner = FactoryPlanner()

    assert planner.plan({}) == []
