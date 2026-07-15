from ai.factory.runtime_recovery import (
    FactoryRuntimeRecovery,
)


class FakeRuntime:
    def __init__(self):
        self.running = False


class FakeState:
    def restore(self):
        return {
            "cycle": 5,
        }


def test_restart():
    runtime = FakeRuntime()

    recovery = FactoryRuntimeRecovery(
        runtime=runtime
    )

    result = recovery.restart()

    assert result["status"] == "SUCCESS"
    assert runtime.running is True


def test_restore():
    recovery = FactoryRuntimeRecovery(
        state=FakeState()
    )

    result = recovery.restore()

    assert result["state"]["cycle"] == 5


def test_critical_recovery():
    recovery = FactoryRuntimeRecovery()

    result = recovery.recover(
        {
            "level": "CRITICAL",
        }
    )

    assert result["action"] == "RESTART"


def test_history():
    recovery = FactoryRuntimeRecovery()

    recovery.restart()

    assert len(recovery.history()) == 1
