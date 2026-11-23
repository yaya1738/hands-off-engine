import json

import ai.ai_runner as ai_runner


def test_execute_command_fails_closed_without_governed_authority(monkeypatch):
    def forbidden_run(*args, **kwargs):
        raise AssertionError("AI Runner must never reach subprocess.run")

    monkeypatch.setattr(ai_runner.subprocess, "run", forbidden_run)

    result = ai_runner.execute_command("echo should-not-run")

    assert result["status"] == "blocked"
    assert result["returncode"] == -1
    assert "governed execution authority" in result["reason"].lower()


def test_execute_environment_flag_cannot_enable_generated_shell_commands(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    results = tmp_path / "results"
    processed = tmp_path / "processed"
    tasks.mkdir()
    task_file = tasks / "test.json"
    task_file.write_text(json.dumps({
        "id": "test",
        "goal": "test execution boundary",
        "context": {"files": [], "notes": ""},
        "mode": "plan-and-execute",
    }))

    monkeypatch.setattr(ai_runner, "EXECUTE", True)
    monkeypatch.setattr(ai_runner, "RESULTS_DIR", results)
    monkeypatch.setattr(ai_runner, "PROCESSED_DIR", processed)
    monkeypatch.setattr(
        ai_runner,
        "call_llm",
        lambda system, user: {"plan": "run a harmless command", "commands": ["echo no-op"]},
    )

    def forbidden_run(*args, **kwargs):
        raise AssertionError("AI_RUNNER_EXECUTE must not authorize subprocess execution")

    monkeypatch.setattr(ai_runner.subprocess, "run", forbidden_run)

    ai_runner.process_task(task_file)

    result = json.loads((results / "test.result.json").read_text())
    assert result["status"] == "failed"
    assert result["command_results"][0]["status"] == "blocked"
    assert not task_file.exists()
    assert (processed / "test.json").exists()
