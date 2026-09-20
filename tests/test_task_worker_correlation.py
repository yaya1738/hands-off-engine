import json
from pathlib import Path


def test_process_task_preserves_correlation_id(monkeypatch, tmp_path):
    import scripts.task_worker as worker

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "msg-1",
        "context": {
            "task_id": "task-42",
            "action": "health_check",
            "reply_to": "corr-99",
        },
    }

    result = worker.process_task(task)

    assert result["context"]["task_id"] == "task-42"
    assert result["context"]["reply_to"] == "corr-99"
    assert result["context"]["correlation_id"] == "corr-99"


def test_process_task_falls_back_to_task_id_correlation(monkeypatch, tmp_path):
    import scripts.task_worker as worker

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "msg-2",
        "context": {
            "task_id": "task-43",
            "action": "health_check",
        },
    }

    result = worker.process_task(task)

    assert result["context"]["correlation_id"] == "task-43"


def test_poll_once_respects_max_tasks(monkeypatch, tmp_path):
    import scripts.task_worker as worker

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(worker, "RESULTS", tmp_path / "task_results.jsonl")
    monkeypatch.setattr(worker, "load_processed", lambda: set())
    monkeypatch.setattr(worker, "_load_result_ids", lambda: set())
    monkeypatch.setattr(worker, "save_processed", lambda _: None)
    monkeypatch.setattr(worker, "_publish_result_to_bus", lambda _: None)
    monkeypatch.setattr(worker, "get_emitter", lambda: None)
    monkeypatch.setattr(worker, "factory_control", None)

    tasks = [
        {
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "msg_id": "msg-bound-1",
            "context": {
                "task_id": "bound-task-1",
                "action": "health_check",
            },
        },
        {
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "msg_id": "msg-bound-2",
            "context": {
                "task_id": "bound-task-2",
                "action": "health_check",
            },
        },
    ]

    monkeypatch.setattr(worker, "_iter_canonical_assignments", lambda: iter(tasks))

    processed = []

    def fake_process(task):
        processed.append(task["context"]["task_id"])
        return {
            "from": "anyclaw",
            "to": "factory",
            "type": "task_result",
            "msg_id": task["context"]["task_id"],
            "context": {
                "task_id": task["context"]["task_id"],
                "status": "success",
                "result": {"health": "ok"},
                "correlation_id": task["context"]["task_id"],
            },
        }

    monkeypatch.setattr(worker, "process_task", fake_process)

    class FakeLock:
        def __init__(self, task_id):
            self.task_id = task_id

        def try_acquire(self):
            return True

        def release(self):
            pass

    monkeypatch.setattr(worker, "TaskLock", FakeLock)

    assert worker.poll_once(max_tasks=1) == 1
    assert processed == ["bound-task-1"]


def test_poll_once_can_target_specific_task(monkeypatch, tmp_path):
    import scripts.task_worker as worker

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(worker, "RESULTS", tmp_path / "task_results.jsonl")
    monkeypatch.setattr(worker, "load_processed", lambda: set())
    monkeypatch.setattr(worker, "_load_result_ids", lambda: set())
    monkeypatch.setattr(worker, "save_processed", lambda _: None)
    monkeypatch.setattr(worker, "_publish_result_to_bus", lambda _: None)
    monkeypatch.setattr(worker, "get_emitter", lambda: None)
    monkeypatch.setattr(worker, "factory_control", None)

    tasks = []
    for n in ("older", "target"):
        tasks.append({
            "from": "factory",
            "to": "anyclaw",
            "type": "task_assignment",
            "msg_id": f"msg-{n}",
            "context": {"task_id": f"control-{n}", "action": "health_check"},
        })

    monkeypatch.setattr(worker, "_iter_canonical_assignments", lambda: iter(tasks))

    processed = []

    def fake_process(task):
        processed.append(task["context"]["task_id"])
        return {
            "from": "anyclaw", "to": "factory", "type": "task_result",
            "msg_id": task["context"]["task_id"],
            "context": {
                "task_id": task["context"]["task_id"],
                "status": "success",
                "result": {"health": "ok"},
                "correlation_id": task["context"]["task_id"],
            },
        }

    monkeypatch.setattr(worker, "process_task", fake_process)

    class FakeLock:
        def __init__(self, task_id): pass
        def try_acquire(self): return True
        def release(self): pass

    monkeypatch.setattr(worker, "TaskLock", FakeLock)

    assert worker.poll_once(max_tasks=1, task_id="control-target") == 1
    assert processed == ["control-target"]
