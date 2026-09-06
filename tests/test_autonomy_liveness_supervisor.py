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


class FakeGateway:
    def execute_autonomous(self, objective):
        return {
            "decision": {"status": "READY"},
            "execution": {"success": True, "steps_completed": ["execution"]},
        }


def test_run_cycle_executes_selected_objective_without_consumer(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", lambda runtime=None: FakeGateway())

    result = supervisor.run_cycle(tmp_path)

    assert result["status"] == "observed"
    assert result["task_queued"] is True
    assert result["execution_observed"] is True
    assert result["verification_observed"] is True
    assert result["live_system_active"] is True
    assert result["task_id"]
    assert len((tmp_path / "state" / "autonomous_tasks_completed.jsonl").read_text()) > 0


def test_successful_objective_is_retired_from_future_selection(tmp_path: Path):
    completed = tmp_path / "state" / "autonomous_tasks_completed.jsonl"
    completed.parent.mkdir(parents=True)
    completed.write_text(
        '{"task":{"metadata":{"objective":"already completed"}},'
        '"result":"{\"status\":\"executed\",\"success\":true}"}\n',
        encoding="utf-8",
    )

    assert supervisor._successful_objectives(tmp_path) == {"already completed"}


def test_failed_objective_is_not_retired(tmp_path: Path):
    completed = tmp_path / "state" / "autonomous_tasks_completed.jsonl"
    completed.parent.mkdir(parents=True)
    completed.write_text(
        '{"task":{"metadata":{"objective":"retry me"}},'
        '"result":"{\"status\":\"executed\",\"success\":false}"}\n',
        encoding="utf-8",
    )

    assert supervisor._successful_objectives(tmp_path) == set()


def test_persist_writes_liveness_state(tmp_path: Path):
    supervisor.persist(tmp_path, {"status": "observed", "timestamp": "now"})
    assert (tmp_path / "state" / "autonomy_liveness.json").exists()
