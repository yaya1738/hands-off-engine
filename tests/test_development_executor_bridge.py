from ai.factory.development_executor import FactoryDevelopmentExecutor


def test_development_executor_uses_bounded_agent_seam():
    executor = FactoryDevelopmentExecutor(
        lambda envelope: {
            "status": "executed",
            "objective": envelope["task"]["objective"],
        }
    )
    result = executor.execute({"id": 1, "objective": "improve factory"})
    assert result["status"] == "executed"
    assert result["objective"] == "improve factory"
