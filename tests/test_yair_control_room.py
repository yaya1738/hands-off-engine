import json

from scripts import yair_control_room as room


def test_read_events_reads_valid_json_and_skips_bad_lines(tmp_path, monkeypatch):
    bus = tmp_path / "messages.jsonl"
    bus.write_text(json.dumps({"from": "anyclaw", "to": "factory", "type": "task_result", "timestamp": "now"}) + "\nBAD\n")
    monkeypatch.setattr(room, "BUS", bus)
    events = room.read_events()
    assert len(events) == 1
    assert events[0]["type"] == "task_result"


def test_read_events_empty_when_bus_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(room, "BUS", tmp_path / "missing.jsonl")
    assert room.read_events() == []
