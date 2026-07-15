from ai.factory.runner import FactoryRunner


def test_runner_executes_steps():
    runner = FactoryRunner()

    result = runner.run(
        "factory-001",
        [
            "analyze",
            "implement",
            "test",
        ],
    )

    assert result.status == "SUCCESS"
    assert len(result.commands) == 3
    assert "all steps completed" in result.outputs


def test_runner_empty_steps():
    runner = FactoryRunner()

    result = runner.run(
        "factory-002",
        [],
    )

    assert result.status == "SUCCESS"
