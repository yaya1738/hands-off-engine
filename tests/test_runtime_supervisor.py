from ai.factory.runtime_supervisor import (
    FactoryRuntimeSupervisor,
)


class FakeRuntime:
    def __init__(self):
        self.running = False


def test_check():
    supervisor = FactoryRuntimeSupervisor(
        FakeRuntime()
    )

    result = supervisor.check()

    assert result["running"] is False


def test_monitor():
    supervisor = FactoryRuntimeSupervisor(
        FakeRuntime()
    )

    result = supervisor.monitor()

    assert result["action"] == "RESTART_REQUIRED"


def test_recover():
    runtime = FakeRuntime()

    supervisor = FactoryRuntimeSupervisor(
        runtime
    )

    result = supervisor.recover()

    assert result["action"] == "RECOVERED"
    assert runtime.running is True


def test_history():
    supervisor = FactoryRuntimeSupervisor(
        FakeRuntime()
    )

    supervisor.check()

    assert len(supervisor.history()) == 1
