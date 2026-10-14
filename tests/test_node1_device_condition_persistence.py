import json

from scripts import node1_runtime


def test_device_condition_persists_without_changing_runtime_health(monkeypatch, tmp_path):
    state_file = tmp_path / "node1_state.json"
    monkeypatch.setattr(node1_runtime, "NODE_STATE", state_file)
    state = node1_runtime.NodeState()
    state.data["health"] = "healthy"
    snapshot = {"battery_percent": 50, "charging": True}
    assessment = {"status": "normal", "warnings": [], "concerns": []}

    state.record_device_condition(snapshot, assessment)

    saved = json.loads(state_file.read_text())
    assert saved["health"] == "healthy"
    assert saved["device_condition"]["snapshot"] == snapshot
    assert saved["device_condition"]["assessment"]["status"] == "normal"
    assert len(saved["device_condition_history"]) == 1
    assert saved["device_condition"]["observed_at"]


def test_device_condition_history_is_bounded(monkeypatch, tmp_path):
    state_file = tmp_path / "node1_state.json"
    monkeypatch.setattr(node1_runtime, "NODE_STATE", state_file)
    state = node1_runtime.NodeState()

    for value in range(30):
        state.record_device_condition(
            {"battery_percent": value},
            {"status": "normal", "warnings": [], "concerns": []},
        )

    saved = json.loads(state_file.read_text())
    assert len(saved["device_condition_history"]) == 24
    assert saved["device_condition"]["snapshot"]["battery_percent"] == 29
