from datetime import datetime, timezone

from scripts import executor as executor_module


def _command(mode="LIVE", **extra):
    command = {
        "id": "authority-boundary-test",
        "mode": mode,
        "approval_status": "approved",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "target": "executor",
        "payload": {"action": "trade", "params": {"amount": 1}},
    }
    command.update(extra)
    return command


def test_legacy_executor_never_executes_live_even_with_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_module, "EXECUTION_LOG", tmp_path / "execution.jsonl")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "rate_limit.json")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "rate_limit.json")
    executor = executor_module.Executor(repo_root=tmp_path)

    def forbidden_live_execute(command):
        raise AssertionError("LIVE backend must not be reached")

    monkeypatch.setattr(executor, "_live_execute", forbidden_live_execute)
    result = executor.execute_command(_command())

    assert result.status == "rejected"
    assert "does not grant execution_enabled" in result.error


def test_legacy_executor_rejects_unknown_mode_instead_of_falling_through(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_module, "EXECUTION_LOG", tmp_path / "execution.jsonl")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "rate_limit.json")
    executor = executor_module.Executor(repo_root=tmp_path)

    def forbidden_live_execute(command):
        raise AssertionError("Unknown modes must not reach LIVE backend")

    monkeypatch.setattr(executor, "_live_execute", forbidden_live_execute)
    result = executor.execute_command(_command(mode="AUTOMATIC"))

    assert result.status == "rejected"
    assert "Unsupported execution mode" in result.error


def test_legacy_executor_keeps_dryrun_available(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_module, "EXECUTION_LOG", tmp_path / "execution.jsonl")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "rate_limit.json")
    executor = executor_module.Executor(repo_root=tmp_path)

    result = executor.execute_command(_command(mode="DRYRUN"))

    assert result.status == "dryrun"
    assert result.result["mode"] == "DRYRUN"
