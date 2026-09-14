import json, sys, os
from pathlib import Path

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autonomous.governed_authority import authorize, AuthorityDecision


# ── authority contract tests ──

def test_live_without_approval_is_blocked():
    decision = authorize({"id": "c1", "mode": "LIVE"})
    assert decision.decision == "approval_required"
    assert decision.execution_enabled is False


def test_approved_live_still_does_not_grant_executor_authority():
    decision = authorize({"id": "c2", "mode": "LIVE", "approval_status": "approved"})
    assert decision.decision == "approved"
    assert decision.execution_enabled is False


def test_dryrun_is_non_executing():
    decision = authorize({"id": "c3", "mode": "DRYRUN"})
    assert decision.decision == "dryrun_only"
    assert decision.execution_enabled is False


def test_unknown_mode_fails_closed():
    decision = authorize({"id": "c4", "mode": "UNKNOWN"})
    assert decision.decision == "rejected"


def test_missing_id_fails_closed():
    decision = authorize({})
    assert decision.decision == "rejected"


def test_default_mode_is_dryrun():
    decision = authorize({"id": "c5"})
    assert decision.decision == "dryrun_only"


def test_decision_to_dict():
    decision = authorize({"id": "c6", "mode": "LIVE"})
    d = decision.to_dict()
    assert isinstance(d, dict)
    assert d["command_id"] == "c6"
    assert d["decision"] == "approval_required"


def test_live_approved_still_requires_executor():
    decision = authorize({"id": "c7", "mode": "LIVE", "approval_status": "approved"})
    assert decision.approval_required is True


# ── listener integration tests ──

def test_listener_rejects_unknown_action():
    from scripts.system_listener_inline import process_command
    result = process_command({"id": "x1", "action": "bogus"})
    assert "error" in result
    assert "Unknown action" in result["error"]


def test_listener_query_works():
    from scripts.system_listener_inline import process_command
    result = process_command({"id": "x2", "action": "query", "payload": {"query": "status"}})
    assert result["query"] == "status"
    assert "response" in result


def test_listener_dryrun_execute():
    from scripts.system_listener_inline import process_command
    result = process_command({"id": "x3", "action": "execute", "mode": "DRYRUN", "payload": {"action": "trade"}})
    assert result.get("dryrun") is True
    assert "DRYRUN" in result.get("message", "")


def test_listener_live_execute_goes_to_approval():
    import tempfile, os
    tmp_state = Path(tempfile.mkdtemp())
    try:
        import scripts.system_listener_inline as listener
        orig = listener.STATE_DIR
        listener.STATE_DIR = tmp_state
        listener.QUEUE_FILE = tmp_state / "command_queue.jsonl"
        listener.RESULTS_FILE = tmp_state / "results.jsonl"
        listener.APPROVAL_FILE = tmp_state / "approval_queue.json"

        result = listener.process_command({"id": "x4", "action": "execute", "mode": "LIVE", "payload": {"action": "trade"}})
        assert result.get("command_status") == "awaiting_approval"

        # Verify it appeared in the approval queue
        q = json.loads(listener.APPROVAL_FILE.read_text())
        assert any(p["id"] == "x4" for p in q["pending"])

        listener.STATE_DIR = orig
    finally:
        import shutil
        shutil.rmtree(tmp_state)


def test_listener_rejects_malformed_mode():
    from scripts.system_listener_inline import process_command
    result = process_command({"id": "x5", "action": "execute", "mode": "BANANA"})
    assert result.get("command_status") == "failed"


# ── control API approval workflow tests ──

def test_control_api_approve_reject_flow():
    import tempfile, shutil
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        sys.path.insert(0, str(tmp_dir))
        from scripts.control_api import SystemControl

        # Patch state dir
        sc = SystemControl.__new__(SystemControl)
        sc.repo_root = tmp_dir
        sc.state_dir = tmp_dir / "state"
        sc.state_dir.mkdir(exist_ok=True)
        sc.queue_file = sc.state_dir / "command_queue.jsonl"
        sc.results_file = sc.state_dir / "results.jsonl"
        sc.approval_file = sc.state_dir / "approval_queue.json"

        # Seed a pending approval entry directly
        q = {"pending": [{"id": "test-cmd-1", "action": "execute", "mode": "LIVE"}], "approved": [], "rejected": []}
        sc.approval_file.write_text(json.dumps(q, indent=2) + "\n")

        # Approve
        result = sc.approve("test-cmd-1")
        assert result["status"] == "approved"

        # Should no longer be pending
        assert len(sc.list_pending_approval()) == 0

        # Reject a non-existent one
        result2 = sc.reject("test-cmd-999")
        assert result2["status"] == "not_found"

    finally:
        shutil.rmtree(tmp_dir)


# ── execution gate tests ──

def test_live_approved_with_gate_still_execution_disabled():
    """Even with approval AND gate=True, execution_enabled stays False."""
    decision = authorize(
        {"id": "g1", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=True,
    )
    assert decision.execution_enabled is False
    assert decision.decision == "approved"
    assert "gate active" in decision.reason


def test_live_approved_gate_none_keeps_gate_absent():
    decision = authorize(
        {"id": "g2", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=None,
    )
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason


def test_live_approved_gate_false_keeps_gate_absent():
    decision = authorize(
        {"id": "g3", "mode": "LIVE", "approval_status": "approved"},
        execution_gate=False,
    )
    assert decision.execution_enabled is False
    assert "gate absent" in decision.reason


def test_dryrun_ignores_gate_parameter():
    decision = authorize(
        {"id": "g4", "mode": "DRYRUN"},
        execution_gate=True,
    )
    assert decision.execution_enabled is False
    assert decision.decision == "dryrun_only"
