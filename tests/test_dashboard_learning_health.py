"""Tests for dashboard, learning loop, health monitor, self-improvement."""
import json
from pathlib import Path


def test_dashboard_runs(tmp_path, monkeypatch):
    import scripts.dashboard as dash
    monkeypatch.setattr(dash, "ROOT", tmp_path)
    monkeypatch.setattr(dash, "BUS", tmp_path / "ai" / "coordination" / "messages.jsonl")
    monkeypatch.setattr(dash, "STATE", tmp_path / "state")
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    dash.main()


def test_learning_loop_analyzes_bus(tmp_path, monkeypatch):
    from scripts import learning_loop
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    bus.parent.mkdir(parents=True, exist_ok=True)
    bus.write_text(
        json.dumps({"type": "task_result", "from": "anyclaw", "message": json.dumps({"task_id": "t1", "status": "success"})}) + "\n"
        + json.dumps({"type": "task_result", "from": "anyclaw", "message": json.dumps({"task_id": "t2", "status": "success"})}) + "\n"
        + json.dumps({"type": "task_result", "from": "anyclaw", "message": json.dumps({"task_id": "t3", "status": "error"})}) + "\n"
    )
    monkeypatch.setattr(learning_loop, "BUS", bus)
    monkeypatch.setattr(learning_loop, "STATE", tmp_path / "state.json")
    state = learning_loop.run_analysis()
    assert state["patterns"]["total_tasks"] == 3
    assert state["patterns"]["success_count"] == 2
    assert state["patterns"]["failure_count"] == 1


def test_learning_loop_empty_bus(tmp_path, monkeypatch):
    from scripts import learning_loop
    empty_bus = tmp_path / "empty_bus.jsonl"
    empty_bus.write_text("")
    monkeypatch.setattr(learning_loop, "BUS", empty_bus)
    monkeypatch.setattr(learning_loop, "STATE", tmp_path / "state.json")
    state = learning_loop.run_analysis()
    assert state["patterns"]["total_tasks"] == 0


def test_health_monitor_checks_services(tmp_path, monkeypatch):
    from scripts import health_monitor
    monkeypatch.setattr(health_monitor, "ROOT", tmp_path)
    monkeypatch.setattr(health_monitor, "STATE", tmp_path / "state")
    monkeypatch.setattr(health_monitor, "HEALTH_LOG", tmp_path / "state" / "health_log.jsonl")
    monkeypatch.setattr(health_monitor, "TOKEN_FILE", tmp_path / "no_token.json")
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    result = health_monitor.run_health_check()
    assert "healthy" in result
    assert "checks" in result


def test_self_improvement_generates_tasks(tmp_path, monkeypatch):
    from scripts import self_improvement
    monkeypatch.setattr(self_improvement, "ROOT", tmp_path)
    monkeypatch.setattr(self_improvement, "STATE", tmp_path / "state")
    monkeypatch.setattr(self_improvement, "BUS", tmp_path / "no_bus")
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    state = self_improvement.run()
    assert state["total"] >= 1
    assert all("title" in imp for imp in state["improvements"])


def test_sender_validation_rejects_unknown(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from comm_hub import CommHub
    hub = CommHub(tmp_path)
    result = hub.receive("nonexistent_party", "test", {"msg": "hello"})
    assert result.get("routed_to") == "rejected"
    assert "Unknown sender" in result.get("error", "")


def test_sender_validation_accepts_known(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from comm_hub import CommHub
    hub = CommHub(tmp_path)
    result = hub.receive("operator", "status_query", {})
    assert result.get("routed_to") != "rejected"
