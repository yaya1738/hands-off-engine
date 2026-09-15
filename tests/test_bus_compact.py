import json, tempfile, shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_bus(tmp, events):
    bus = tmp / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True, exist_ok=True)
    bus.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return bus


def test_dedup_removes_duplicate_events():
    from scripts.bus_compact import compact
    tmp = Path(tempfile.mkdtemp())
    events = [
        {"msg_id": "m1", "type": "a"},
        {"msg_id": "m2", "type": "b"},
        {"msg_id": "m1", "type": "a"},  # duplicate
    ]
    bus = _make_bus(tmp, events)
    result = compact(bus_path=bus, max_blocker_age=None)
    assert result["before"] == 3
    assert result["after_dedup"] == 2
    assert result["removed"] == 1
    lines = bus.read_text().strip().split("\n")
    assert len(lines) == 2
    shutil.rmtree(tmp)


def test_stale_blockers_removed():
    from scripts.bus_compact import compact
    tmp = Path(tempfile.mkdtemp())
    old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    events = [
        {"msg_id": "b1", "type": "continuation_event", "context": {"event_type": "blocker"}, "timestamp": old},
        {"msg_id": "m1", "type": "task_assignment"},
        {"msg_id": "b2", "type": "continuation_event", "context": {"event_type": "blocker"}, "timestamp": recent},
    ]
    bus = _make_bus(tmp, events)
    result = compact(bus_path=bus, max_blocker_age=timedelta(hours=24))
    assert result["after"] == 2
    lines = bus.read_text().strip().split("\n")
    remaining = [json.loads(l)["msg_id"] for l in lines]
    assert "b1" not in remaining
    assert "b2" in remaining
    assert "m1" in remaining
    shutil.rmtree(tmp)


def test_dry_run_does_not_modify_bus():
    from scripts.bus_compact import compact
    tmp = Path(tempfile.mkdtemp())
    events = [{"msg_id": "m1"}, {"msg_id": "m1"}]
    bus = _make_bus(tmp, events)
    original = bus.read_text()
    result = compact(bus_path=bus, dry_run=True)
    assert result["dry_run"] is True
    assert bus.read_text() == original
    shutil.rmtree(tmp)
