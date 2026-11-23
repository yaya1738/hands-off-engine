from datetime import datetime
import autonomous.self_healer as self_healer


def test_self_healer_does_not_execute_process_metadata_as_shell(monkeypatch):
    healer = self_healer.SelfHealer.__new__(self_healer.SelfHealer)
    healer.healing_history = []
    healer.restart_counts = {}
    process = self_healer.ProcessGuard(
        name="untrusted-process",
        command="touch /tmp/self-healer-injection; id",
        working_dir="/tmp",
    )

    def forbidden_run(*args, **kwargs):
        raise AssertionError("SelfHealer must not execute process metadata")

    def forbidden_popen(*args, **kwargs):
        raise AssertionError("SelfHealer must not spawn process metadata")

    monkeypatch.setattr(self_healer.subprocess, "run", forbidden_run)
    monkeypatch.setattr(self_healer.subprocess, "Popen", forbidden_popen)
    monkeypatch.setattr(healer, "_log", lambda *args, **kwargs: None)

    assert healer.restart_process(process) is False
    assert healer.healing_history[-1].success is False
    assert healer.healing_history[-1].details["status"] == "blocked"
    assert healer.restart_counts == {}
