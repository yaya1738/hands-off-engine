from ai.factory.runtime_supervisor import (
    FactoryRuntimeSupervisor,
)


class FakeRecovery:
    def restore(self):
        return {
            "status": "RESTORED",
        }


def test_monitor():
    supervisor = FactoryRuntimeSupervisor()

    result = supervisor.monitor(
        {
            "scheduler": True,
            "loop": True,
        }
    )

    assert result["healthy"] is True


def test_detect_failure():
    supervisor = FactoryRuntimeSupervisor()

    result = supervisor.detect(
        {
            "healthy": False,
        }
    )

    assert result["failure"] is True


def test_recover():
    supervisor = FactoryRuntimeSupervisor(
        recovery=FakeRecovery()
    )

    result = supervisor.recover()

    assert result["status"] == "RESTORED"


def test_history():
    supervisor = FactoryRuntimeSupervisor()

    supervisor.monitor(
        {
            "runtime": True,
        }
    )

    assert len(supervisor.history()) == 1
