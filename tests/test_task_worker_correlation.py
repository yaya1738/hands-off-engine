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
