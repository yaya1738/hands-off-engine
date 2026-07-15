from ai.factory.service import (
    FactoryService,
)


class FakeShell:
    def execute_command(
        self,
        command,
    ):
        return {
            "command": command,
            "ok": True,
        }


def test_handle_command():
    service = FactoryService(
        FakeShell()
    )

    result = service.handle(
        "status"
    )

    assert result["command"] == "status"
    assert result["ok"] is True


def test_health():
    service = FactoryService(
        FakeShell()
    )

    result = service.health()

    assert result["status"] == "running"
