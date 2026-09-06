from pathlib import Path

import tools.autonomy_liveness_supervisor as supervisor


class FakeRuntime:
    class Autonomy:
        @staticmethod
        def discovery_gate(objective, context):
            return {"capability_graph_analysis": {"gaps": []}}

    autonomy = Autonomy()


class FakeLoop:
    def __init__(self, runtime):
        self.runtime = runtime

    def select_next(self, context):
        return {
            "selected": {
                "objective": "advance autonomous operation",
                "strategic_objective_id": "adaptive-human-independence",
                "score": 100,
            }
        }


class FakeGateway:
    calls = []

    def __init__(self, runtime=None):
        self.runtime = runtime

    def execute_autonomous(self, objective):
        self.calls.append(objective)
        return {
            "decision": {"status": "READY"},
            "execution": {
                "success": True,
                "steps_completed": ["planning", "execution"],
            },
        }


def test_liveness_cycle_executes_selected_objective_without_consumer_ui(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", FakeGateway)

    state = supervisor.run_cycle(tmp_path)

    assert FakeGateway.calls == ["advance autonomous operation"]
    assert state["execution_observed"] is True
    assert state["verification_observed"] is True
    assert state["live_system_active"] is True
    assert state["claim_basis"] == "observed execution and runtime completion result"
    assert state["task_queued"] is True
    assert state["task_id"] is not None
    assert supervisor.AutonomousTaskQueue(tmp_path).get_all_tasks() == []
