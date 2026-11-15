import json
from datetime import datetime, timezone, timedelta

from autonomous.governed_authority import authorize
from scripts.command_approval import command_fingerprint
from scripts.control_api import SystemControl
from scripts.task_worker import validate_task_envelope, process_task


def _approved_command(tmp_path, command_id="factory-live-1"):
    control = SystemControl(repo_root=tmp_path)
    control.submit_command(
        action="execute",
        target="factory",
        payload={"action": "factory_execute", "objective": "inspect runtime"},
        mode="LIVE",
        sync=False,
    )
    queued = json.loads(control.queue_file.read_text().splitlines()[0])
    queued["id"] = command_id
    control.queue_file.write_text(json.dumps(queued) + "\n")
    queued_at = datetime.now(timezone.utc).isoformat()
    control.approval_file.write_text(json.dumps({
        "pending": [{
            "id": command_id, "action": "execute", "target": "factory",
            "payload": queued["payload"], "mode": "LIVE", "queued_at": queued_at,
        }],
        "approved": [], "rejected": [],
    }))
    assert control.approve(command_id)["status"] == "approved"
    command = json.loads(control.queue_file.read_text().splitlines()[0])
    return control, command


def test_factory_authority_requires_independent_approval_record(tmp_path):
    command = {
        "id": "flag-only", "mode": "LIVE", "approval_status": "approved",
        "objective": "inspect runtime",
    }
    decision = authorize(command, execution_gate=True, approval_file=tmp_path / "missing.json")
    assert decision.decision == "approval_required"
    assert "unavailable" in decision.reason


def test_factory_authority_accepts_systemcontrol_approval(tmp_path):
    control, command = _approved_command(tmp_path)
    decision = authorize(command, execution_gate=True, approval_file=control.approval_file)
    assert decision.decision == "approved"
    assert decision.execution_enabled is False


def test_factory_authority_rejects_payload_tampering(tmp_path):
    control, command = _approved_command(tmp_path)
    command["payload"]["objective"] = "different objective"
    decision = authorize(command, execution_gate=True, approval_file=control.approval_file)
    assert decision.decision == "approval_required"
    assert "mismatch" in decision.reason


def test_factory_authority_rejects_top_level_objective_tampering(tmp_path):
    control, command = _approved_command(tmp_path)
    command["objective"] = "different objective"
    decision = authorize(command, execution_gate=True, approval_file=control.approval_file)
    assert decision.decision == "approval_required"
    assert "mismatch" in decision.reason


def test_factory_authority_rejects_duplicate_approval_records(tmp_path):
    control, command = _approved_command(tmp_path)
    queue = json.loads(control.approval_file.read_text())
    queue["approved"].append(dict(queue["approved"][0]))
    control.approval_file.write_text(json.dumps(queue))
    decision = authorize(command, execution_gate=True, approval_file=control.approval_file)
    assert decision.decision == "approval_required"
    assert "ambiguous" in decision.reason


def test_factory_authority_rejects_expired_approval(tmp_path):
    control, command = _approved_command(tmp_path)
    queue = json.loads(control.approval_file.read_text())
    queue["approved"][0]["approved_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=25)
    ).isoformat()
    control.approval_file.write_text(json.dumps(queue))
    decision = authorize(command, execution_gate=True, approval_file=control.approval_file)
    assert decision.decision == "approval_required"
    assert "expired" in decision.reason


def test_task_worker_rejects_live_factory_envelope_even_with_approved_flag():
    task = {
        "from": "factory", "to": "anyclaw", "type": "task_assignment",
        "msg_id": "msg-live", "context": {
            "task_id": "task-live", "action": "factory_execute",
            "objective": "inspect runtime", "mode": "LIVE",
            "approval_status": "approved",
        },
    }
    valid, reason = validate_task_envelope(task)
    assert not valid
    assert "canonical SystemControl command queue" in reason


def test_task_worker_direct_live_factory_invocation_is_blocked(tmp_path, monkeypatch):
    import scripts.task_worker as worker
    monkeypatch.setattr(worker, "REPO_ROOT", tmp_path)
    task = {
        "from": "factory", "to": "anyclaw", "type": "task_assignment",
        "msg_id": "msg-live-direct", "context": {
            "task_id": "task-live-direct", "action": "factory_execute",
            "objective": "inspect runtime", "mode": "LIVE",
            "approval_status": "approved", "params": {},
        },
    }
    result = process_task(task)
    assert result["context"]["status"] == "blocked"
    assert "canonical SystemControl command queue" in result["context"]["error"]
