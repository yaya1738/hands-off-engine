from scripts.factory_governed_proposal import build_governed_proposal


def test_proposal_is_not_authority():
    result = build_governed_proposal({
        "available": True,
        "diagnosis": "interaction_degradation",
        "observation_complete": True,
        "assessment": {"objective": "improve interaction reliability"},
        "authority": {"decision": "approved"},
    })
    proposal = result["proposal"]
    assert proposal["requires_governance"] is True
    assert proposal["execution_enabled"] is False
    assert proposal["objective"] == "improve interaction reliability"


def test_proposal_preserves_correlation_identity():
    result = build_governed_proposal({
        "available": True,
        "diagnosis": "interaction_degradation",
        "observation_complete": True,
        "assessment": {"objective": "improve interaction reliability"},
        "authority": {
            "msg_id": "msg-123",
            "reply_to": "msg-99",
            "task_id": "task-7",
        },
    })
    assert result["proposal"]["correlation"] == {
        "msg_id": "msg-123",
        "reply_to": "msg-99",
        "task_id": "task-7",
    }


def test_incomplete_reasoning_remains_non_executable():
    result = build_governed_proposal({
        "available": True,
        "diagnosis": "observation_incomplete",
        "observation_complete": False,
    })
    assert result["proposal"]["requires_governance"] is True
    assert result["proposal"]["execution_enabled"] is False


def test_missing_reasoning_fails_closed():
    assert build_governed_proposal(None) == {"available": False}
    assert build_governed_proposal({"available": True}) == {"available": False}
