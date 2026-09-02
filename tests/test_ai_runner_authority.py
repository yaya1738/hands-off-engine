import importlib


def test_ai_runner_legacy_execution_is_blocked(monkeypatch):
    module = importlib.import_module("ai.ai_runner")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess execution must not be reached")

    monkeypatch.setattr(module.subprocess, "run", fail_if_called)

    result = module.execute_command("echo should-never-run")

    assert result["status"] == "blocked"
    assert result["authority"] == "FactoryAuthorityGateway"
    assert result["returncode"] == -1
