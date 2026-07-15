from ai.factory.resilience_controller import (
    FactoryResilienceController,
)


class FakeHealth:
    def status(self, runtime):
        return {
            "status": "DOWN",
        }


class FakeAlerts:
    def check(self, health):
        return {
            "level": "CRITICAL",
        }


class FakeRecovery:
    def recover(self, alert):
        return {
            "action": "RESTART",
        }


def build_controller():
    return FactoryResilienceController(
        health=FakeHealth(),
        alerts=FakeAlerts(),
        recovery=FakeRecovery(),
    )


def test_evaluate():
    controller = build_controller()

    result = controller.evaluate(
        {
            "running": False,
        }
    )

    assert result["alert"]["level"] == "CRITICAL"


def test_respond():
    controller = build_controller()

    result = controller.respond(
        {
            "alert": {
                "level": "CRITICAL",
            }
        }
    )

    assert result["action"] == "RESTART"


def test_history():
    controller = build_controller()

    controller.evaluate({})

    assert len(controller.history()) == 1
