from ai.factory.shell import FactoryShell


class FakeController:
    def inspect(self):
        return {
            "status": "HEALTHY",
        }

    def optimize(self):
        return {
            "action": "continue",
        }

    def latest_state(self):
        return {
            "version": 1,
        }


def test_status_command():
    shell = FactoryShell(
        FakeController()
    )

    result = shell.execute_command(
        "status"
    )

    assert result["status"] == "HEALTHY"


def test_optimize_command():
    shell = FactoryShell(
        FakeController()
    )

    result = shell.execute_command(
        "optimize"
    )

    assert result["action"] == "continue"


def test_unknown_command():
    shell = FactoryShell(
        FakeController()
    )

    result = shell.execute_command(
        "invalid"
    )

    assert result["error"] == "unknown_command"
