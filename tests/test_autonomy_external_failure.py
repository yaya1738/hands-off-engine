import json

import tools.autonomy_liveness_supervisor as supervisor


class _QuietAutonomy:
    def discovery_gate(self, *_args, **_kwargs):
        return {"capability_graph_analysis": {"gaps": []}}


class _Runtime:
    autonomy = _QuietAutonomy()


class _RetryableExternalQueue:
    def __init__(self, _repo_root):
        self.task = {
            "id": "external-retry-1",
            "title": "Process authenticated external request",
            "description": "process retryable external request",
            "priority": "high",
            "source": "github_issue_autonomous_ingress",
            "metadata": {"objective_id": "external-request-retry"},
        }
        self.attempts = []
        self.completed = []

    def get_next_task(self):
        return self.task

    def get_all_tasks(self):
        return [self.task]

    def record_attempt(self, task_id, result):
        self.attempts.append((task_id, result))

    def complete_task(self, task_id, result):
        self.completed.append((task_id, result))
        raise AssertionError("failed external work must not be completed")


class _FailingGateway:
    def __init__(self, **_kwargs):
        pass

    def execute_autonomous(self, objective):
        return {
            "execution": {
                "success": False,
                "steps_completed": [],
            },
            "objective": objective,
            "reason": "retryable governed execution failure",
        }


def test_failed_external_wakeup_does_not_claim_convergence_or_discard_work(tmp_path, monkeypatch):
    mission_path = tmp_path / "state" / "autonomy_mission.json"
    mission_path.parent.mkdir(parents=True)
    mission_path.write_text(
        json.dumps(
            {
                "mission": "persistent mission",
                "cycle_count": 24,
                "last_status": "converged",
                "last_error": None,
                "converged": True,
            }
        )
    )

    queue = _RetryableExternalQueue(tmp_path)
    monkeypatch.setattr(supervisor, "FactoryRuntime", _Runtime)
    monkeypatch.setattr(supervisor, "AutonomousTaskQueue", lambda _root: queue)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", _FailingGateway)

    state = supervisor.run_cycle(tmp_path)

    assert state["external_task_processed"] is True
    assert state["converged"] is False
    assert state["execution_observed"] is True
    assert state["verification_observed"] is True
    assert state["execution_succeeded"] is False
    assert state["live_system_active"] is False
    assert state["status"] == "observed"
    assert state["mission"]["last_status"] == "blocked_or_failed"
    assert state["mission"]["converged"] is False
    assert queue.attempts and queue.attempts[0][0] == "external-retry-1"
    assert not queue.completed

    persisted = json.loads(mission_path.read_text())
    assert persisted["converged"] is False
    assert persisted["last_status"] == "blocked_or_failed"
    assert persisted["last_error"] == "retryable governed execution failure"
