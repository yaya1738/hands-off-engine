import json

import tools.autonomy_liveness_supervisor as supervisor


class _FakeAutonomy:
    def discovery_gate(self, *_args, **_kwargs):
        return {"capability_graph_analysis": {"gaps": []}}


class _FakeRuntime:
    autonomy = _FakeAutonomy()


class _FakeQueue:
    def __init__(self, _repo_root):
        self.tasks = []
        self.completed = []

    def get_next_task(self):
        return None

    def get_all_tasks(self):
        return self.tasks

    def add_task(self, **kwargs):
        task_id = "reactivation-task"
        self.tasks.append({"id": task_id, "metadata": kwargs["metadata"]})
        return task_id

    def complete_task(self, task_id, result):
        self.completed.append((task_id, result))

    def record_attempt(self, *_args, **_kwargs):
        raise AssertionError("successful reactivation must complete the task")


class _FailIfExecutedGateway:
    def __init__(self, **_kwargs):
        pass

    def execute_autonomous(self, _objective):
        raise AssertionError("converged cycle must not execute an objective")


class _SuccessfulGateway:
    def __init__(self, **_kwargs):
        pass

    def execute_autonomous(self, objective):
        return {
            "execution": {
                "success": True,
                "steps_completed": ["execution", "learning"],
            },
            "objective": objective,
        }


class _ReactivatedObjectiveLoop:
    def __init__(self, _runtime):
        pass

    def select_next(self, _context):
        return {
            "status": "selected",
            "candidate_count": 1,
            "candidates": [{"objective": "repair newly discovered gap", "score": 99}],
            "selected": {
                "objective": "repair newly discovered gap",
                "strategic_objective_id": "gap-1",
                "score": 99,
            },
        }


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


def test_run_cycle_reactivates_after_new_actionable_gap(tmp_path, monkeypatch):
    mission_path = tmp_path / "state" / "autonomy_mission.json"
    mission_path.parent.mkdir(parents=True)
    mission_path.write_text(
        json.dumps(
            {
                "mission": "old mission value is normalized",
                "cycle_count": 7,
                "last_status": "converged",
                "last_error": None,
                "converged": True,
            }
        )
    )

    class _ActionableAutonomy:
        def discovery_gate(self, *_args, **_kwargs):
            return {"capability_graph_analysis": {"gaps": [{"capability": "new_gap"}]}}

    class _ActionableRuntime:
        autonomy = _ActionableAutonomy()

    queue = _FakeQueue(tmp_path)
    monkeypatch.setattr(supervisor, "FactoryRuntime", _ActionableRuntime)
    monkeypatch.setattr(supervisor, "AutonomousTaskQueue", lambda _root: queue)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", _ReactivatedObjectiveLoop)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", _SuccessfulGateway)
    monkeypatch.setattr(supervisor, "_successful_objectives", lambda _root: set())

    state = supervisor.run_cycle(tmp_path)

    assert state["converged"] is False
    assert state["execution_observed"] is True
    assert state["verification_observed"] is True
    assert state["execution_succeeded"] is True
    assert state["live_system_active"] is True
    assert state["mission"]["last_status"] == "succeeded"
    assert state["mission"]["convergence_transition"] is False
    assert state["mission"]["converged"] is False
    assert state["task_queued"] is True
    assert state["task_id"] == "reactivation-task"
    assert queue.completed

    persisted = json.loads(mission_path.read_text())
    assert persisted["converged"] is False
    assert persisted["last_status"] == "succeeded"
