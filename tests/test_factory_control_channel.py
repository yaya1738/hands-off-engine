from pathlib import Path

from tools import factory_control_channel as channel


def test_shared_control_root_round_trip(tmp_path, monkeypatch):
    control = tmp_path / "shared-control"
    monkeypatch.setenv("FACTORY_CONTROL_ROOT", str(control))
    repo = tmp_path / "repo"
    repo.mkdir()

    command = channel.append_command(
        repo,
        "improve the runtime",
        source="factory",
        idempotency_key="cmd-1",
    )
    assert command["idempotency_key"] == "cmd-1"
    assert channel.pending_commands(repo)[0]["id"] == command["id"]

    result = channel.append_result(
        repo,
        command["id"],
        status="completed",
        result={"success": True},
        correlation_id="corr-1",
    )
    assert result["command_id"] == command["id"]
    assert channel.pending_results(repo)[0]["status"] == "completed"

    state = channel.publish_state(repo, node_id="node1", status="ready")
    assert state["node_id"] == "node1"
    assert channel.load_state(repo)["status"] == "ready"
    assert not (repo / "state" / "factory_control_commands.jsonl").exists()


def test_default_root_remains_repo_state(tmp_path, monkeypatch):
    monkeypatch.delenv("FACTORY_CONTROL_ROOT", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    channel.append_command(repo, "local command", idempotency_key="local-1")
    assert (repo / "state" / "factory_control_commands.jsonl").exists()
