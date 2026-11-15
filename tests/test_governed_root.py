import json
from datetime import datetime, timezone
from pathlib import Path

import autonomous.governed_root as root
from autonomous.governed_authority import authorize
from scripts.command_approval import command_fingerprint


def _isolated(tmp_path):
    root.set_repo_root(tmp_path)
    (tmp_path / "state").mkdir(exist_ok=True)


def _seed_approved(tmp_path, command_id):
    command = {
        "id": command_id, "source": "test", "action": "execute", "target": "factory",
        "payload": {"action": "factory_execute", "objective": "inspect runtime"},
        "mode": "LIVE", "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": 5, "sync": False, "timeout_seconds": 300,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "approval_status": "approved", "status": "pending",
    }
    fingerprint = command_fingerprint(command)
    command["approval_fingerprint"] = fingerprint
    root._resolve_queue().write_text(json.dumps(command) + "\n")
    root._resolve_approvals().write_text(json.dumps({
        "pending": [],
        "approved": [{
            "id": command_id,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "fingerprint": fingerprint,
        }],
        "rejected": [],
    }))
    return command


def test_record_decisions_persists_fail_closed_state(tmp_path):
    _isolated(tmp_path)
    root._resolve_queue().write_text(
        json.dumps({"id": "live-1", "action": "execute", "mode": "LIVE", "status": "pending"}) + "\n"
    )
    decisions = root.record_decisions()
    assert decisions["live-1"]["decision"] == "approval_required"
    assert decisions["live-1"]["execution_enabled"] is False
    assert json.loads(root._resolve_decisions().read_text()) == decisions


def test_record_decisions_tracks_durable_approval_without_enabling_execution(tmp_path):
    _isolated(tmp_path)
    _seed_approved(tmp_path, "live-2")
    decisions = root.record_decisions()
    assert decisions["live-2"]["decision"] == "approved"
    assert decisions["live-2"]["execution_enabled"] is False
    assert decisions["live-2"]["approval_required"] is True


def test_record_decisions_ignores_malformed_queue_lines(tmp_path):
    _isolated(tmp_path)
    root._resolve_queue().write_text("not-json\n" + json.dumps({"id": "dry-1", "status": "pending"}) + "\n")
    decisions = root.record_decisions()
    assert decisions["dry-1"]["decision"] == "dryrun_only"
    assert decisions["dry-1"]["execution_enabled"] is False


def test_set_repo_root_changes_all_paths(tmp_path):
    root.set_repo_root(tmp_path)
    assert root.repo_root() == tmp_path
    assert root._resolve_status() == tmp_path / "state" / "governed_root_status.json"
    assert root._resolve_queue() == tmp_path / "state" / "command_queue.jsonl"
    assert root._resolve_decisions() == tmp_path / "state" / "governed_decisions.json"


def test_isolated_instances_do_not_share_state(tmp_path):
    root_a, root_b = tmp_path / "instance_a", tmp_path / "instance_b"
    for path in (root_a, root_b):
        (path / "state").mkdir(parents=True, exist_ok=True)
    root.set_repo_root(root_a)
    root._resolve_queue().write_text(json.dumps({"id": "a-1", "status": "pending"}) + "\n")
    root.record_decisions()
    root.set_repo_root(root_b)
    assert "a-1" not in root.record_decisions()
    root.set_repo_root(root_a)
    assert "a-1" in root.load_decisions()


def test_state_dir_created_automatically(tmp_path):
    path = tmp_path / "nonexistent" / "deep"
    root.set_repo_root(path)
    (path / "state").mkdir(parents=True, exist_ok=True)
    root._resolve_queue().write_text(json.dumps({"id": "z-1", "status": "pending"}) + "\n")
    root.record_decisions()
    assert root._resolve_decisions().exists()


def test_live_approved_without_gate_records_no_execution(tmp_path):
    _isolated(tmp_path)
    _seed_approved(tmp_path, "gate-1")
    decisions = root.record_decisions()
    assert decisions["gate-1"]["execution_enabled"] is False
    assert decisions["gate-1"]["decision"] == "approved"


def test_live_approved_with_gate_still_no_execution(tmp_path):
    _isolated(tmp_path)
    command = _seed_approved(tmp_path, "gate-2")
    decision = authorize(command, execution_gate=True, approval_file=root._resolve_approvals())
    assert decision.execution_enabled is False
    assert decision.decision == "approved"
    assert "gate active" in decision.reason


def test_live_gate_absent_still_requires_no_execution(tmp_path):
    _isolated(tmp_path)
    command = _seed_approved(tmp_path, "gate-3")
    decision = authorize(command, execution_gate=None, approval_file=root._resolve_approvals())
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason


def test_live_gate_false_still_requires_no_execution(tmp_path):
    _isolated(tmp_path)
    command = _seed_approved(tmp_path, "gate-4")
    decision = authorize(command, execution_gate=False, approval_file=root._resolve_approvals())
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason
