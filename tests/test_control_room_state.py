import json
from pathlib import Path

from scripts.control_room_state import build_snapshot


def test_snapshot_uses_canonical_bus_and_lifecycle(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    lifecycle = tmp_path / "state" / "task_lifecycle.json"
    bus.parent.mkdir(parents=True)
    lifecycle.parent.mkdir(parents=True)
    bus.write_text(json.dumps({"type": "task_result", "context": {"task_id": "t-1"}}) + "\n")
    lifecycle.write_text(json.dumps({"t-1": {"task_id": "t-1", "states": {"completed": "now"}}}))
    snapshot = build_snapshot(tmp_path, bus_limit=1, lifecycle_limit=1)
    assert snapshot["source_of_truth"] == "ai/coordination/messages.jsonl"
    assert snapshot["bus"]["event_count"] == 1
    assert snapshot["lifecycle"]["tasks"]["t-1"]["states"]["completed"] == "now"


def test_snapshot_is_bounded_and_read_only(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text("\n".join(json.dumps({"type": "x", "n": i}) for i in range(5)) + "\n")
    before = bus.read_text()
    snapshot = build_snapshot(tmp_path, bus_limit=2, lifecycle_limit=0)
    assert snapshot["bus"]["event_count"] == 2
    assert [e["n"] for e in snapshot["bus"]["events"]] == [3, 4]
    assert snapshot["lifecycle"]["task_count"] == 0
    assert bus.read_text() == before
