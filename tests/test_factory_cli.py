from ai.factory.cli import FactoryCLI


def test_cli_status():
    cli = FactoryCLI()

    result = cli.status()

    assert result["factory"] == "active"


def test_cli_run():
    cli = FactoryCLI()

    result = cli.run(
        "cli-test-001",
        "test factory command",
    )

    assert result["task_id"] == "cli-test-001"


def test_cli_history():
    cli = FactoryCLI()

    cli.run(
        "cli-test-002",
        "store history",
    )

    history = cli.history()

    assert len(history) >= 1
