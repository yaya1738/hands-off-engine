from pathlib import Path

from tools import autonomy_liveness_supervisor as supervisor


class FakeRuntime:
    class Autonomy:
        @staticmethod
        def discovery_gate(objective, context):
            return {
                "capability_graph_analysis": {"gaps": ["close autonomous execution handoff"]}
            }

    def __init__(self):
        self.autonomy = self.Autonomy()


class FakeLoop:
    def __init__(self, runtime):
        self.runtime = runtime

    def select_next(self, context):
        return {
            "status": "selected",
            "selected": {
                "objective": "close autonomous execution handoff",
                "strategic_objective_id": "adaptive-human-independence",
                "score": 95,
            },
        }


def test_run_cycle_queues_selected_objective_once(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)

    first = supervisor.run_cycle(tmp_path)
    second = supervisor.run_cycle(tmp_path)

    assert first["status"] == "active"
    assert first["task_queued"] is True
    assert first["task_id"]
    assert second["task_queued"] is False
    assert len((tmp_path / "state" / "autonomous_task_queue.json").read_text()) > 0


def test_persist_writes_liveness_state(tmp_path: Path):
    supervisor.persist(tmp_path, {"status": "active", "timestamp": "now"})
    assert (tmp_path / "state" / "autonomy_liveness.json").exists()
