from ai.factory.recovery_manager import (
    FactoryRecoveryManager,
)


def test_recovery_success():
    manager = FactoryRecoveryManager()

    manager.register_recovery(
        "scheduler",
        lambda: "restarted",
    )

    result = manager.recover(
        "scheduler"
    )

    assert result["status"] == "RECOVERED"
    assert result["output"] == "restarted"


def test_no_handler():
    manager = FactoryRecoveryManager()

    result = manager.recover(
        "missing"
    )

    assert result["status"] == "NO_HANDLER"


def test_history():
    manager = FactoryRecoveryManager()

    manager.recover(
        "unknown"
    )

    assert len(manager.history()) == 1
