import json

import tools.autonomy_liveness_supervisor as supervisor


class _QuietAutonomy:
    def discovery_gate(self, *_args, **_kwargs):
        return {"capability_graph_analysis": {"gaps": []}}


class _Runtime:
    autonomy = _QuietAutonomy()


class _ExternalTaskQueue:
    def __init__(self, _repo_root):
        self.completed = []

    def get_next_task(self):
        return {
            "id": "external-1",
            "title": "Process authenticated external request",
            "description": "process newly arrived external autonomous request",
            "priority": "high",
            "source": "github_issue_autonomous_ingress",
            "metadata": {"objective_id": "external-request-1"},
        }

    def get_all_tasks(self):
        return [self.get_next_task()]

    def complete_task(self, task_id, result):
        self.completed.append((task_id, result))

    def record_attempt(self, *_args, **_kwargs):
        raise AssertionError("successful external reactivation must complete the task")


class _SuccessfulGateway:
    def __init__(self, **_kwargs):
        pass

    def execute_autonomous(self, objective):
        return {
            "execution": {
                "success": True,
                "steps_completed": ["execution", "verification"],
            },
            "objective": objective,
        }


def test_converged_system_reactivates_for_pending_external_task(tmp_path, monkeypatch):
    mission_path = tmp_path / "state" / "autonomy_mission.json"
    mission_path.parent.mkdir(parents=True)
    mission_path.write_text(
        json.dumps(
            {
                "mission": "old mission value is normalized",
                "cycle_count": 23,
                "last_status": "converged",
                "last_error": None,
                "converged": True,
            }
        )
    )

    queue = _ExternalTaskQueue(tmp_path)
    monkeypatch.setattr(supervisor, "FactoryRuntime", _Runtime)
    monkeypatch.setattr(supervisor, "AutonomousTaskQueue", lambda _root: queue)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", _SuccessfulGateway)

    state = supervisor.run_cycle(tmp_path)

    assert state["converged"] is False
    assert state["external_task_processed"] is True
    assert state["task_queued"] is False
    assert state["task_id"] == "external-1"
    assert state["execution_observed"] is True
    assert state["verification_observed"] is True
    assert state["execution_succeeded"] is True
    assert state["live_system_active"] is True
    assert state["mission"]["converged"] is False
    assert state["mission"]["convergence_transition"] is False
    assert queue.completed and queue.completed[0][0] == "external-1"

    persisted = json.loads(mission_path.read_text())
    assert persisted["converged"] is False
    assert persisted["last_status"] == "succeeded"
