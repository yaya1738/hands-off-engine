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

def test_poll_once_forwards_only_explicit_human_contact_metadata(monkeypatch, tmp_path):
    """An explicitly authored request reaches the continuation emitter unchanged."""
    import scripts.task_worker as worker

    contact = {
        "participant_id": "reviewer-1",
        "task": {
            "task_id": "task-human-44",
            "human_contact_reason": "material_ambiguity",
            "summary": "Two safe approaches remain.",
            "human_question": "Which approach should Factory implement?",
            "human_question_impact": "The answer changes the implementation plan.",
        },
    }
    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "assignment-human-44",
        "context": {
            "task_id": "task-human-44",
            "action": "health_check",
            "human_contact": contact,
        },
    }

    class Lock:
        def __init__(self, task_id):
            self.task_id = task_id
        def try_acquire(self):
            return True
        def release(self):
            pass

    class Emitter:
        calls = []
        def emit_task_completed(self, **kwargs):
            self.calls.append(kwargs)

    emitter = Emitter()
    monkeypatch.setattr(worker, "_iter_canonical_assignments", lambda: iter([task]))
    monkeypatch.setattr(worker, "load_processed", lambda: set())
    monkeypatch.setattr(worker, "_load_result_ids", lambda: set())
    monkeypatch.setattr(worker, "TaskLock", Lock)
    monkeypatch.setattr(worker, "get_emitter", lambda: emitter)
    monkeypatch.setattr(worker, "save_processed", lambda processed: None)
    monkeypatch.setattr(worker, "_publish_result_to_bus", lambda result: True)
    monkeypatch.setattr(worker, "RESULTS", tmp_path / "state" / "task_results.jsonl")
    monkeypatch.setattr(worker, "PROCESSED_IDS", tmp_path / "state" / "processed.json")

    assert worker.poll_once(max_tasks=1) == 1
    assert len(emitter.calls) == 1
    assert emitter.calls[0]["human_contact"] == contact
    assert emitter.calls[0]["task_id"] == "task-human-44"


def test_poll_once_does_not_infer_human_contact_from_decision_evidence(monkeypatch, tmp_path):
    """Decision/health evidence alone is not promoted into a contact instruction."""
    import scripts.task_worker as worker

    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "assignment-evidence-only",
        "context": {
            "task_id": "task-evidence-only",
            "action": "health_check",
            "factory_decision_context": {
                "assessment": {"gaps": ["missing context"]},
                "authority": {"decision": "pending", "approval_required": True},
                "system_health": {"status": "warn"},
            },
        },
    }

    class Lock:
        def __init__(self, task_id):
            self.task_id = task_id
        def try_acquire(self):
            return True
        def release(self):
            pass

    class Emitter:
        calls = []
        def emit_task_completed(self, **kwargs):
            self.calls.append(kwargs)

    emitter = Emitter()
    monkeypatch.setattr(worker, "_iter_canonical_assignments", lambda: iter([task]))
    monkeypatch.setattr(worker, "load_processed", lambda: set())
    monkeypatch.setattr(worker, "_load_result_ids", lambda: set())
    monkeypatch.setattr(worker, "TaskLock", Lock)
    monkeypatch.setattr(worker, "get_emitter", lambda: emitter)
    monkeypatch.setattr(worker, "save_processed", lambda processed: None)
    monkeypatch.setattr(worker, "_publish_result_to_bus", lambda result: True)
    monkeypatch.setattr(worker, "RESULTS", tmp_path / "state" / "task_results.jsonl")
    monkeypatch.setattr(worker, "PROCESSED_IDS", tmp_path / "state" / "processed.json")

    assert worker.poll_once(max_tasks=1) == 1
    assert len(emitter.calls) == 1
    assert emitter.calls[0]["human_contact"] is None



def test_explicit_contact_flows_from_worker_to_review_proposal_end_to_end(monkeypatch, tmp_path):
    """Exercise the real worker/emitter/router path without transport delivery."""
    import scripts.task_worker as worker
    import scripts.continuation as continuation

    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(worker, "COORDINATION_BUS", tmp_path / "ai" / "coordination" / "messages.jsonl")
    monkeypatch.setattr(worker, "RESULTS", tmp_path / "state" / "task_results.jsonl")
    monkeypatch.setattr(worker, "PROCESSED_IDS", tmp_path / "state" / "processed.json")
    monkeypatch.setattr(continuation, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(continuation, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(continuation, "EVENTS_FILE", tmp_path / "state" / "continuation_events.jsonl")
    monkeypatch.setattr(continuation, "EMITTED_IDS", tmp_path / "state" / "emitted_event_ids.json")

    contact = {
        "participant_id": "reviewer-test",
        "task": {
            "task_id": "task-e2e-1",
            "human_contact_reason": "material_ambiguity",
            "summary": "Two safe approaches remain.",
            "human_question": "Which approach should Factory implement?",
            "human_question_impact": "The answer changes the implementation plan.",
        },
    }
    task = {
        "from": "factory",
        "to": "anyclaw",
        "type": "task_assignment",
        "msg_id": "assignment-e2e-1",
        "message": "Review a material design ambiguity",
        "context": {
            "task_id": "task-e2e-1",
            "action": "health_check",
            "human_contact": contact,
        },
    }

    class Lock:
        def __init__(self, task_id):
            self.task_id = task_id
        def try_acquire(self):
            return True
        def release(self):
            pass

    monkeypatch.setattr(worker, "_iter_canonical_assignments", lambda: iter([task]))
    monkeypatch.setattr(worker, "load_processed", lambda: set())
    monkeypatch.setattr(worker, "_load_result_ids", lambda: set())
    monkeypatch.setattr(worker, "TaskLock", Lock)
    monkeypatch.setattr(worker, "save_processed", lambda processed: None)
    monkeypatch.setattr(worker, "_publish_result_to_bus", lambda result: True)
    monkeypatch.setattr(worker, "process_task", lambda task: {
        "id": task["context"]["task_id"],
        "context": {
            "task_id": task["context"]["task_id"],
            "status": "blocked",
            "result": "Waiting for a human decision",
            "correlation_id": task["context"]["task_id"],
        },
    })
    monkeypatch.setattr(worker, "get_emitter", continuation.ContinuationEmitter)

    assert worker.poll_once(max_tasks=1) == 1
    bus = tmp_path / "ai" / "coordination" / "messages.jsonl"
    records = [json.loads(line) for line in bus.read_text().splitlines()]
    proposals = [record for record in records if record.get("type") == "human_contact_proposal"]
    assert len(proposals) == 1
    assert proposals[0]["context"]["participant_id"] == "reviewer-test"
    assert proposals[0]["context"]["payload"]["task_id"] == "task-e2e-1"
    assert proposals[0]["context"]["send_authorized"] is False
    assert proposals[0]["context"]["requires_policy_check"] is True
    assert not any(record.get("type") == "email_sent" for record in records)
