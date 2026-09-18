def test_in_progress_factory_result_is_preserved_and_wakeable():
    import scripts.continuation as continuation

    emitter = continuation.ContinuationEmitter.__new__(continuation.ContinuationEmitter)
    emitter.emitted_ids = set()
    event = emitter.emit_task_completed(
        "task-in-progress", "in_progress", "Factory execution already active"
    )

    assert event is not None
    assert event["event_type"] == "in_progress"
    assert event["is_wake"] is True
    assert event["context"]["status"] == "in_progress"


def test_in_progress_task_result_is_not_collapsed_to_error(monkeypatch, tmp_path):
    import scripts.task_worker as worker

    class FakeAdapter:
        @staticmethod
        def execute_factory_command(command, execution_gate=True):
            return {
                "status": "in_progress",
                "command_id": command["id"],
                "correlation_id": command["correlation_id"],
            }

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    monkeypatch.setitem(__import__("sys").modules, "scripts.factory_execution_adapter", FakeAdapter)

    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "msg-in-progress",
        "context": {
            "task_id": "task-in-progress",
            "action": "factory_execute",
            "objective": "continue bounded convergence",
            "mode": "LIVE",
            "approval_status": "approved",
            "reply_to": "corr-in-progress",
            "params": {},
        },
    }

    result = worker.process_task(task)

    assert result["context"]["status"] == "in_progress"
    assert result["context"]["correlation_id"] == "corr-in-progress"
