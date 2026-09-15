import json
import subprocess
import sys
from pathlib import Path

from scripts.control_room_state import build_snapshot


def test_snapshot_uses_canonical_bus_and_lifecycle(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    lifecycle = tmp_path / "state" / "task_lifecycle.json"
    bus.parent.mkdir(parents=True)
    lifecycle.parent.mkdir(parents=True)

    bus.write_text(
        json.dumps({"type": "task_assignment", "context": {"task_id": "t-1"}})
        + "\n"
        + json.dumps({"type": "task_result", "context": {"task_id": "t-1"}})
        + "\n"
    )
    lifecycle.write_text(json.dumps({"t-1": {"task_id": "t-1", "states": {"completed": "now"}}}))

    snapshot = build_snapshot(tmp_path, bus_limit=1, lifecycle_limit=1)

    assert snapshot["source_of_truth"] == "ai/coordination/messages.jsonl"
    assert snapshot["bus"]["event_count"] == 1
    assert snapshot["bus"]["events"][0]["type"] == "task_result"
    assert snapshot["lifecycle"]["task_count"] == 1
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


def test_snapshot_skips_malformed_bus_tail_until_limit(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_text("\n".join([
        json.dumps({"type": "x", "n": 1}),
        json.dumps({"type": "x", "n": 2}),
        "{partial",
    ]) + "\n")
    before = bus.read_text()
    snapshot = build_snapshot(tmp_path, bus_limit=2, lifecycle_limit=0)
    assert [event["n"] for event in snapshot["bus"]["events"]] == [1, 2]
    assert bus.read_text() == before


def test_snapshot_skips_invalid_utf8_bus_tail_until_limit(tmp_path: Path):
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    bus.write_bytes(
        json.dumps({"type": "x", "n": 1}).encode() + b"\n"
        + json.dumps({"type": "x", "n": 2}).encode() + b"\n"
        + b"{\xffinvalid}\n"
    )
    snapshot = build_snapshot(tmp_path, bus_limit=2, lifecycle_limit=0)
    assert [event["n"] for event in snapshot["bus"]["events"]] == [1, 2]


def test_lifecycle_limit_selects_newest_by_updated_at(tmp_path: Path):
    lifecycle = tmp_path / "state" / "task_lifecycle.json"
    lifecycle.parent.mkdir(parents=True)
    lifecycle.write_text(json.dumps({
        "aaa-old": {"updated_at": "2026-09-15T00:00:00+00:00", "states": {"sent": "old"}},
        "zzz-new": {"updated_at": "2026-09-15T02:00:00+00:00", "states": {"completed": "new"}},
        "mmm-mid": {"updated_at": "2026-09-15T01:00:00+00:00", "states": {"claimed": "mid"}},
    }))
    snapshot = build_snapshot(tmp_path, bus_limit=0, lifecycle_limit=2)
    tasks = snapshot["lifecycle"]["tasks"]
    assert list(tasks) == ["zzz-new", "mmm-mid"]
    assert "aaa-old" not in tasks


def test_lifecycle_current_state_uses_declared_precedence(tmp_path: Path):
    lifecycle = tmp_path / "state" / "task_lifecycle.json"
    lifecycle.parent.mkdir(parents=True)
    lifecycle.write_text(json.dumps({
        "t-1": {
            "updated_at": "2026-09-15T03:00:00+00:00",
            "states": {
                "sent": "1",
                "completed": "2",
                "result_published": "3",
            },
        }
    }))
    snapshot = build_snapshot(tmp_path, bus_limit=0, lifecycle_limit=1)
    assert snapshot["lifecycle"]["tasks"]["t-1"]["current_state"] == "result_published"


def test_snapshot_cli_bootstraps_repo_imports(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "scripts/control_room_state.py", "--repo-root", str(tmp_path), "--bus-limit", "0", "--lifecycle-limit", "0"],
        capture_output=True,
        text=True,
        check=True,
    )
    snapshot = json.loads(result.stdout)
    assert snapshot["source_of_truth"] == "ai/coordination/messages.jsonl"
    assert snapshot["bus"]["event_count"] == 0
    assert snapshot["lifecycle"]["task_count"] == 0
