from pathlib import Path

import scripts.comm_hub as comm_hub


def test_commhub_initialization_uses_explicit_repo_root(monkeypatch, tmp_path):
    repo_root = tmp_path / "checkout"
    global_root = tmp_path / "global-sentinel"

    monkeypatch.setattr(comm_hub, "MESSAGES_FILE", global_root / "ai" / "coordination" / "messages.jsonl")
    monkeypatch.setattr(comm_hub, "INBOUND_DIR", global_root / "state" / "inbound")
    monkeypatch.setattr(comm_hub, "OUTBOUND_DIR", global_root / "state" / "outbound")

    comm_hub.CommHub(repo_root=repo_root)

    assert (repo_root / "state").is_dir()
    assert (repo_root / "state" / "inbound").is_dir()
    assert (repo_root / "state" / "outbound").is_dir()
    assert (repo_root / "ai" / "coordination").is_dir()
    assert not global_root.exists()


def test_commhub_file_delivery_uses_checkout_local_outbound(monkeypatch, tmp_path):
    repo_root = tmp_path / "checkout"
    global_root = tmp_path / "global-sentinel"
    monkeypatch.setattr(comm_hub, "OUTBOUND_DIR", global_root / "state" / "outbound")

    hub = comm_hub.CommHub(repo_root=repo_root)
    result = hub._deliver_file({"id": "locality-test", "payload": {"ok": True}}, "anyclaw")

    assert result["status"] == "sent"
    assert not global_root.exists()
    assert list((repo_root / "state" / "outbound").glob("*"))
