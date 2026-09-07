import json
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


class FailedGateway:
    def execute_autonomous(self, objective):
        return {
            "decision": {"status": "READY"},
            "execution": {"success": False, "steps_completed": []},
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
    assert result["execution_succeeded"] is True
    assert result["live_system_active"] is True
    assert result["task_id"]
    assert len((tmp_path / "state" / "autonomous_tasks_completed.jsonl").read_text()) > 0


def test_failed_runtime_execution_is_not_reported_as_live_activity(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)
    monkeypatch.setattr(supervisor, "FactoryAuthorityGateway", lambda runtime=None: FailedGateway())

    result = supervisor.run_cycle(tmp_path)

    assert result["execution_observed"] is True
    assert result["verification_observed"] is True
    assert result["execution_succeeded"] is False
    assert result["live_system_active"] is False


def test_successful_objective_is_retired_from_future_selection(tmp_path: Path):
    completed = tmp_path / "state" / "autonomous_tasks_completed.jsonl"
    completed.parent.mkdir(parents=True)
    completed.write_text(
        json.dumps({
            "task": {"metadata": {"objective": "already completed"}},
            "result": json.dumps({"status": "executed", "success": True}),
        }) + "\n",
        encoding="utf-8",
    )

    assert supervisor._successful_objectives(tmp_path) == {"already completed"}


def test_failed_objective_is_not_retired(tmp_path: Path):
    completed = tmp_path / "state" / "autonomous_tasks_completed.jsonl"
    completed.parent.mkdir(parents=True)
    completed.write_text(
        json.dumps({
            "task": {"metadata": {"objective": "retry me"}},
            "result": json.dumps({"status": "executed", "success": False}),
        }) + "\n",
        encoding="utf-8",
    )

    assert supervisor._successful_objectives(tmp_path) == set()


def test_persist_writes_liveness_state(tmp_path: Path):
    supervisor.persist(tmp_path, {"status": "observed", "timestamp": "now"})
    assert (tmp_path / "state" / "autonomy_liveness.json").exists()


def test_run_once_executes_and_persists_single_cycle(monkeypatch, tmp_path: Path):
    observed = {}

    def fake_cycle(repo_root):
        observed["repo_root"] = repo_root
        return {"timestamp": "now", "status": "observed", "execution_succeeded": True}

    monkeypatch.setattr(supervisor, "run_cycle", fake_cycle)
    monkeypatch.setattr(supervisor.signal, "alarm", lambda *_: None)

    result = supervisor.run_once(tmp_path)

    assert observed["repo_root"] == tmp_path
    assert result["execution_succeeded"] is True
    persisted = (tmp_path / "state" / "autonomy_liveness.json").read_text(encoding="utf-8")
    assert '"execution_succeeded": true' in persisted


def test_pending_external_task_preempts_generated_objective(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(supervisor, "FactoryRuntime", FakeRuntime)
    monkeypatch.setattr(supervisor, "FactoryAutonomousObjectiveLoop", FakeLoop)

    seen = []

    class RecordingGateway:
        def execute_autonomous(self, objective):
            seen.append(objective)
            return {"execution": {"success": True, "steps_completed": ["external"]}}

    monkeypatch.setattr(
        supervisor,
        "FactoryAuthorityGateway",
        lambda runtime=None: RecordingGateway(),
    )

    queue = supervisor.AutonomousTaskQueue(tmp_path)
    task_id = queue.add_task(
        title="External request",
        description="finish work requested through authenticated Telegram",
        priority="critical",
        source="telegram_user",
    )

    result = supervisor.run_cycle(tmp_path)

    assert result["external_task_processed"] is True
    assert result["task_id"] == task_id
    assert seen == ["finish work requested through authenticated Telegram"]
    assert queue.get_all_tasks() == []
