import json

from scripts.control_room_state import build_snapshot


def test_snapshot_exposes_heartbeat_as_fail_closed_telemetry(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "dass_heartbeat_status.json").write_text(
        json.dumps({
            "status": "completed",
            "timestamp": "2026-09-15T00:00:00+00:00",
            "processed_commands": 2,
            "governed_decisions": 2,
            "execution_enabled": True,
            "fail_closed": False,
        })
    )

    snapshot = build_snapshot(tmp_path)
    heartbeat = snapshot["heartbeat"]

    assert heartbeat["available"] is True
    assert heartbeat["status"] == "completed"
    assert heartbeat["processed_commands"] == 2
    assert heartbeat["governed_decisions"] == 2
    assert heartbeat["execution_enabled"] is False
    assert heartbeat["fail_closed"] is True
