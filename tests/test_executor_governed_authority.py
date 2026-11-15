from datetime import datetime, timezone

import scripts.executor as executor_module
from scripts.executor import Executor


def _executor(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_module, "EXECUTION_LOG", tmp_path / "execution.jsonl")
    monkeypatch.setattr(executor_module, "RATE_LIMIT_FILE", tmp_path / "rate-limit.json")
    return Executor(repo_root=tmp_path)


def test_live_executor_requires_authority_execution_grant(tmp_path, monkeypatch):
    executor = _executor(tmp_path, monkeypatch)

    def forbidden_live_execute(command):
        raise AssertionError("LIVE backend must not be reached")

    monkeypatch.setattr(executor, "_live_execute", forbidden_live_execute)
    result = executor.execute_command({
        "id": "live-authority-test",
        "action": "execute",
        "target": "system",
        "mode": "LIVE",
        "approval_status": "approved",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"action": "pause"},
    })

    assert result.status == "rejected"
    assert "Governed authority denied LIVE execution" in result.error


def test_untrusted_execution_enabled_field_cannot_grant_authority(tmp_path, monkeypatch):
    executor = _executor(tmp_path, monkeypatch)

    def forbidden_live_execute(command):
        raise AssertionError("Caller-supplied execution_enabled must not grant authority")

    monkeypatch.setattr(executor, "_live_execute", forbidden_live_execute)
    result = executor.execute_command({
        "id": "spoofed-authority-test",
        "action": "execute",
        "target": "system",
        "mode": "LIVE",
        "approval_status": "approved",
        "execution_enabled": True,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"action": "pause"},
    })

    assert result.status == "rejected"
    assert "Governed authority denied LIVE execution" in result.error


def test_executor_rejects_unknown_mode(tmp_path, monkeypatch):
    executor = _executor(tmp_path, monkeypatch)

    def forbidden_live_execute(command):
        raise AssertionError("Unsupported mode must not reach LIVE backend")

    monkeypatch.setattr(executor, "_live_execute", forbidden_live_execute)
    result = executor.execute_command({
        "id": "unknown-mode-test",
        "action": "execute",
        "target": "system",
        "mode": "AUTONOMOUS",
        "payload": {"action": "pause"},
    })

    assert result.status == "rejected"
    assert "Unsupported execution mode" in result.error
