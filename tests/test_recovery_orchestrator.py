from ai.factory.recovery_orchestrator import (
    FactoryRecoveryOrchestrator,
)


class FakeState:
    def load(self):
        return {
            "status": "RESTORED",
        }


def fake_health():
    return {
        "status": "HEALTHY",
    }


def test_detect():
    recovery = FactoryRecoveryOrchestrator()

    result = recovery.detect(
        {
            "status": "DOWN",
        }
    )

    assert result["needs_recovery"] is True


def test_restore():
    recovery = FactoryRecoveryOrchestrator(
        state_manager=FakeState()
    )

    result = recovery.restore()

    assert result["status"] == "RESTORED"


def test_verify():
    recovery = FactoryRecoveryOrchestrator(
        health_checker=fake_health
    )

    result = recovery.verify()

    assert result["status"] == "HEALTHY"


def test_history():
    recovery = FactoryRecoveryOrchestrator()

    recovery.detect(
        {
            "status": "DOWN",
        }
    )

    assert len(recovery.history()) == 1
