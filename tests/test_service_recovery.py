from ai.factory.service_recovery import (
    FactoryServiceRecovery,
)


class FakeHealth:
    def __init__(self, healthy=True):
        self.healthy = healthy

    def check(self):
        return {
            "healthy": self.healthy,
        }

    def ready(self):
        return {
            "ready": self.healthy,
        }


class FakeService:
    def restart(self):
        return {
            "status": "RESTARTED",
        }


def test_detect_failure():
    recovery = FactoryServiceRecovery(
        health=FakeHealth(False)
    )

    result = recovery.detect()

    assert result["recovery_needed"] is True


def test_recover():
    recovery = FactoryServiceRecovery(
        service=FakeService()
    )

    result = recovery.recover()

    assert result["status"] == "RESTARTED"


def test_verify():
    recovery = FactoryServiceRecovery(
        health=FakeHealth(True)
    )

    result = recovery.verify()

    assert result["ready"] is True


def test_history():
    recovery = FactoryServiceRecovery()

    recovery.detect()

    assert len(recovery.history()) == 1
