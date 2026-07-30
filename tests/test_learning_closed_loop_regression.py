from ai.factory.runtime import FactoryRuntime


def test_learning_failure_reaches_planner():
    r = FactoryRuntime()

    r.learning_loop.record_outcome({
        "action": {
            "type": "autonomous_failure_recovery",
            "failure": {
                "error": "REGRESSION_TEST_FAILURE"
            }
        }
    })

    r.run_improvement_cycle({
        "success": True,
        "steps_completed": []
    })

    history = r.improvement_planner.history()

    assert any(
        "REGRESSION_TEST_FAILURE" in task
        for entry in history
        for task in entry.get("tasks", [])
    )
