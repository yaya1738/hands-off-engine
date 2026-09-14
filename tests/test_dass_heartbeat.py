import json

import autonomous.dass_heartbeat as heartbeat


def test_heartbeat_is_bounded_and_fail_closed(tmp_path):
    heartbeat.STATE = tmp_path
    heartbeat.QUEUE = tmp_path / "command_queue.jsonl"
    heartbeat.DECISIONS = tmp_path / "governed_decisions.json"
    heartbeat.STATUS = tmp_path / "dass_heartbeat_status.json"
    heartbeat.QUEUE.write_text(
        json.dumps({
            "id": "live-1",
            "action": "execute",
            "mode": "LIVE",
            "status": "pending",
        }) + "\n"
    )

    result = heartbeat.heartbeat()

    assert result["status"] == "completed"
    assert result["processed_commands"] == 1
    assert result["execution_enabled"] is False
    persisted = json.loads(heartbeat.DECISIONS.read_text())
    assert persisted["live-1"]["decision"] == "approval_required"
    assert persisted["live-1"]["execution_enabled"] is False
