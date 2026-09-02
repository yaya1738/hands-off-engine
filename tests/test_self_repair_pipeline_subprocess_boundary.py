import importlib


def test_self_repair_pipeline_uses_non_shell_argv(monkeypatch):
    module = importlib.import_module("factory_self_repair_pipeline")
    calls = []

    class Result:
        returncode = 0
        stdout = "{}"
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    goal = 'safe goal; echo INJECTION'
    result = module.run_tool(["python", "worker.py", goal])

    assert result["success"] is True
    assert calls == [
        (
            ["python", "worker.py", goal],
            {
                "shell": False,
                "capture_output": True,
                "text": True,
            },
        )
    ]
