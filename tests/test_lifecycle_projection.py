import json

from scripts.lifecycle_projection import LifecycleProjector, apply_message


def _assignment(task_id="task-1"):
    return {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "msg-1",
        "timestamp": "2026-09-14T10:00:00+00:00",
        "context": {"task_id": task_id, "action": "health_check"},
    }


def _result(task_id="task-1"):
    return {
        "from": "anyclaw",
        "to": "factory",
        "type": "task_result",
        "msg_id": task_id,
        "timestamp": "2026-09-14T10:00:02+00:00",
        "context": {"task_id": task_id, "status": "success", "result": {"health": "ok"}},
    }


def test_projection_preserves_task_id_and_lifecycle(tmp_path):
    projector = LifecycleProjector(repo_root=tmp_path)
    result = projector.project([_assignment(), _result()])

    assert result["tasks"] == 1
    item = projector.get("task-1")
    assert item["sender"] == "factory"
    assert item["recipient"] == "anyclaw"
    assert item["action"] == "health_check"
    assert "sent" in item["states"]
    assert "completed" in item["states"]
    assert "result_published" in item["states"]


def test_projection_is_idempotent(tmp_path):
    projector = LifecycleProjector(repo_root=tmp_path)
    messages = [_assignment(), _result()]
    first = projector.project(messages)
    second = projector.project(messages)

    assert first["changed"] == 1
    assert second["changed"] == 0
    persisted = json.loads((tmp_path / "state" / "task_lifecycle.json").read_text())
    assert list(persisted) == ["task-1"]


def test_apply_message_ignores_non_task_events():
    state = {}
    assert apply_message(state, {"type": "heartbeat", "msg_id": "h1"}) is False
    assert state == {}
