from ai.factory.startup_recovery import (
    FactoryStartupRecovery,
)


class FakeStore:
    def load(self):
        return {
            "mode": "AUTONOMOUS",
        }


def test_restore():
    recovery = FactoryStartupRecovery(
        FakeStore()
    )

    result = recovery.restore()

    assert result["status"] == "RESTORED"
    assert result["state"]["mode"] == "AUTONOMOUS"


def test_validate():
    recovery = FactoryStartupRecovery(
        FakeStore()
    )

    result = recovery.validate(
        {
            "test": True,
        }
    )

    assert result["valid"] is True


def test_startup():
    recovery = FactoryStartupRecovery(
        FakeStore()
    )

    result = recovery.startup()

    assert result["status"] == "READY"


def test_history():
    recovery = FactoryStartupRecovery(
        FakeStore()
    )

    recovery.startup()

    assert len(recovery.history()) == 3
