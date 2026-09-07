import json

import tools.autonomy_liveness_supervisor as supervisor


class _FakeAutonomy:
    def discovery_gate(self, *_args, **_kwargs):
        return {"capability_graph_analysis": {"gaps": []}}


class _FakeRuntime:
    autonomy = _FakeAutonomy()


class _FakeQueue:
    def __init__(self, _repo_root):
        pass

    def get_next_task(self):
        return None


class _FailIfExecutedGateway:
    def __init__(self, **_kwargs):
        pass

    def execute_autonomous(self, _objective):
        raise AssertionError("converged cycle must not execute an objective")


def test_run_cycle_converges_without_creating_or_executing_work(tmp_path, monkeypatch):
    monkeypatch.setattr(supervisor, "FactoryRuntime", _FakeRuntime)
    monkeypatch.setattr(supervisor, "AutonomousTaskQueue", _FakeQueue)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", _FailIfExecutedGateway)

    state = supervisor.run_cycle(tmp_path)

    assert state["status"] == "converged"
    assert state["converged"] is True
    assert state["execution_observed"] is False
    assert state["execution_succeeded"] is False
    assert state["live_system_active"] is True
    assert state["selection"]["status"] == "converged"
    assert state["task_queued"] is False
    assert state["task_id"] is None
    assert state["mission"]["last_status"] == "converged"
    assert state["mission"]["convergence_transition"] is True

    mission = json.loads((tmp_path / "state" / "autonomy_mission.json").read_text())
    assert mission["converged"] is True
