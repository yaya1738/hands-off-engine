from ai.factory.change_validation import FactoryChangeValidation


def test_change_validation_uses_non_shell_subprocess(monkeypatch):
    calls = []

    class Result:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr("ai.factory.change_validation.subprocess.run", fake_run)

    result = FactoryChangeValidation()._run(["python3", "-c", "print('ok')"])

    assert result["success"] is True
    assert calls == [
        (
            ["python3", "-c", "print('ok')"],
            {"shell": False, "capture_output": True, "text": True},
        )
    ]
