from ai.factory.maintenance_planner import (
    FactoryMaintenancePlanner,
)


def test_healthy_plan():
    planner = FactoryMaintenancePlanner()

    result = planner.plan(
        {
            "issues": [],
        }
    )

    assert result["action"] == "CONTINUE_MONITORING"


def test_issue_plan():
    planner = FactoryMaintenancePlanner()

    result = planner.plan(
        {
            "issues": [
                "scheduler",
            ],
        }
    )

    assert result["action"] == "RUN_CHECK"
    assert result["priority"] == "HIGH"


def test_history():
    planner = FactoryMaintenancePlanner()

    planner.plan(
        {
            "issues": [],
        }
    )

    assert len(planner.history()) == 1
