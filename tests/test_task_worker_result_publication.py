import json
from pathlib import Path


def test_task_result_contract_is_canonical_and_idempotent(tmp_path, monkeypatch):
    """A worker result must have one canonical task identity and be appendable once."""
    from scripts import task_worker

    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True)
    results = tmp_path / "state" / "task_results.jsonl"
    results.parent.mkdir(parents=True)
    monkeypatch.setattr(task_worker, "COORDINATION_BUS", bus)
    monkeypatch.setattr(task_worker, "RESULTS", results)

    result = {
        "from": "anyclaw",
        "to": "factory",
        "type": "task_result",
        "msg_id": "task-1",
        "timestamp": "2026-09-14T10:00:02+00:00",
        "context": {
            "task_id": "task-1",
            "status": "success",
            "result": {"health": "ok"},
            "reply_to": "assignment-1",
        },
    }

    task_worker._publish_result_to_bus(result)
    task_worker._publish_result_to_bus(result)

    lines = [json.loads(line) for line in bus.read_text().splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0]["type"] == "task_result"
    assert lines[0]["context"]["task_id"] == "task-1"
    assert lines[0]["context"]["reply_to"] == "assignment-1"
