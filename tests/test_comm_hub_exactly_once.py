from pathlib import Path

from scripts.comm_hub import CommHub


def test_messages_jsonl_send_writes_one_canonical_entry(tmp_path):
    hub = CommHub(repo_root=tmp_path)
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"

    result = hub.send(
        "anyclaw",
        "coordination",
        {"task_id": "task-exactly-once", "message": "hello"},
        channel_override="messages_jsonl",
    )

    assert result["status"] == "sent"
    lines = [line for line in bus.read_text().splitlines() if line.strip()]
    assert len(lines) == 1

    entry = __import__("json").loads(lines[0])
    assert entry["type"] == "coordination"
    assert entry["msg_id"] == result["id"]


def test_explicit_repo_root_isolated_for_party_registry(tmp_path):
    hub = CommHub(repo_root=tmp_path)
    hub.register_party(
        "isolated-test-party",
        "Isolated Test Party",
        "agent",
        ["file"],
    )

    local_registry = tmp_path / "state" / "party_registry.json"
    assert local_registry.exists()
    assert "isolated-test-party" in local_registry.read_text()


def test_explicit_repo_root_isolated_for_comm_log(tmp_path):
    hub = CommHub(repo_root=tmp_path)
    hub._log_outbound({"id": "local-only"}, {"status": "ok"})

    local_log = Path(tmp_path) / "state" / "comm_log.jsonl"
    assert local_log.exists()
    assert "local-only" in local_log.read_text()
