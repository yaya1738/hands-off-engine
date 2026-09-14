from autonomous.governed_authority import authorize


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
