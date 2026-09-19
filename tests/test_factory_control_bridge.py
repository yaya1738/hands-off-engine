from __future__ import annotations

import json

from scripts import factory_control_bridge as bridge
from tools import factory_control_channel


def test_bridge_admits_one_safe_command(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_CONTROL_ROOT", str(tmp_path / "shared"))
    monkeypatch.setattr(bridge, "CLAIMED", tmp_path / "claimed.json")
    monkeypatch.setattr(bridge, "BUS", tmp_path / "messages.jsonl")

    command = factory_control_channel.append_command(
        tmp_path / "repo",
        "report current system status",
        source="factory",
        idempotency_key="canary-1",
        metadata={"action": "system_status", "params": {"reason": "shared_canary"}},
    )

    assert bridge.poll_once(max_commands=1) == 1
    task = json.loads(bridge.BUS.read_text().strip())
    assert task["context"]["action"] == "system_status"
    assert task["context"]["factory_control_command_id"] == command["id"]


def test_bridge_rejects_factory_execution(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_CONTROL_ROOT", str(tmp_path / "shared"))
    monkeypatch.setattr(bridge, "CLAIMED", tmp_path / "claimed.json")
    monkeypatch.setattr(bridge, "BUS", tmp_path / "messages.jsonl")

    factory_control_channel.append_command(
        tmp_path / "repo",
        "execute Factory objective",
        source="factory",
        idempotency_key="live-1",
        metadata={"action": "factory_execute", "params": {"objective": "x"}},
    )

    assert bridge.poll_once(max_commands=1) == 0
    assert not bridge.BUS.exists()
