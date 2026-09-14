import json
from pathlib import Path

import autonomous.governed_root as root


def _isolated(tmp_path):
    """Point governed_root at a temporary directory for test isolation."""
    root.set_repo_root(tmp_path)
    (tmp_path / "state").mkdir(exist_ok=True)


def test_record_decisions_persists_fail_closed_state(tmp_path):
    _isolated(tmp_path)
    queue = root._resolve_queue()
    queue.write_text(
        json.dumps({"id": "live-1", "action": "execute", "mode": "LIVE", "status": "pending"}) + "\n"
    )

    decisions = root.record_decisions()

    assert decisions["live-1"]["decision"] == "approval_required"
    assert decisions["live-1"]["execution_enabled"] is False
    persisted = json.loads(root._resolve_decisions().read_text())
    assert persisted == decisions


def test_record_decisions_tracks_explicit_approval_without_enabling_execution(tmp_path):
    _isolated(tmp_path)
    queue = root._resolve_queue()
    queue.write_text(
        json.dumps({
            "id": "live-2",
            "action": "execute",
            "mode": "LIVE",
            "approval_status": "approved",
            "status": "pending",
        }) + "\n"
    )

    decisions = root.record_decisions()

    assert decisions["live-2"]["decision"] == "approved"
    assert decisions["live-2"]["execution_enabled"] is False
    assert decisions["live-2"]["approval_required"] is True


def test_record_decisions_ignores_malformed_queue_lines(tmp_path):
    _isolated(tmp_path)
    queue = root._resolve_queue()
    queue.write_text("not-json\n" + json.dumps({"id": "dry-1", "status": "pending"}) + "\n")

    decisions = root.record_decisions()

    assert decisions["dry-1"]["decision"] == "dryrun_only"
    assert decisions["dry-1"]["execution_enabled"] is False


# ── instance-root isolation tests ──

def test_set_repo_root_changes_all_paths(tmp_path):
    root.set_repo_root(tmp_path)
    assert root.repo_root() == tmp_path
    assert root._resolve_status() == tmp_path / "state" / "governed_root_status.json"
    assert root._resolve_queue() == tmp_path / "state" / "command_queue.jsonl"
    assert root._resolve_decisions() == tmp_path / "state" / "governed_decisions.json"


def test_isolated_instances_do_not_share_state(tmp_path):
    root_a = tmp_path / "instance_a"
    root_b = tmp_path / "instance_b"
    for p in [root_a, root_b]:
        (p / "state").mkdir(parents=True, exist_ok=True)

    # Instance A
    root.set_repo_root(root_a)
    (root._resolve_queue()).write_text(
        json.dumps({"id": "a-1", "status": "pending"}) + "\n"
    )
    root.record_decisions()

    # Instance B — should not see A's state
    root.set_repo_root(root_b)
    decisions_b = root.record_decisions()
    assert "a-1" not in decisions_b

    # Instance A still has it
    root.set_repo_root(root_a)
    decisions_a = root.load_decisions()
    assert "a-1" in decisions_a


def test_state_dir_created_automatically(tmp_path):
    root.set_repo_root(tmp_path / "nonexistent" / "deep")
    (tmp_path / "nonexistent" / "deep" / "state").mkdir(parents=True, exist_ok=True)
    queue = root._resolve_queue()
    queue.write_text(json.dumps({"id": "z-1", "status": "pending"}) + "\n")
    root.record_decisions()
    assert root._resolve_decisions().exists()


# ── LIVE rejection when execution gate is absent/false ──

def test_live_approved_without_gate_records_no_execution(tmp_path):
    _isolated(tmp_path)
    queue = root._resolve_queue()
    queue.write_text(
        json.dumps({
            "id": "gate-1",
            "mode": "LIVE",
            "approval_status": "approved",
            "status": "pending",
        }) + "\n"
    )
    decisions = root.record_decisions()
    assert decisions["gate-1"]["execution_enabled"] is False
    assert decisions["gate-1"]["decision"] == "approved"


def test_live_approved_with_gate_still_no_execution(tmp_path):
    from autonomous.governed_authority import authorize

    decision = authorize(
        {"id": "gate-2", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=True,
    )
    assert decision.execution_enabled is False
    assert decision.decision == "approved"
    assert "gate active" in decision.reason


def test_live_rejected_when_gate_absent(tmp_path):
    from autonomous.governed_authority import authorize

    decision = authorize(
        {"id": "gate-3", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=None,
    )
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason


def test_live_rejected_when_gate_false(tmp_path):
    from autonomous.governed_authority import authorize

    decision = authorize(
        {"id": "gate-4", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=False,
    )
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason
