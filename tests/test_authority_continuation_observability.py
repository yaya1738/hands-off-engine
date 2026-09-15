from scripts.authority_continuation_observability import project_authority_continuation


def test_approved_decision_allows_continuation_but_not_execution():
    result = project_authority_continuation({
        "authority_decision": {
            "available": True,
            "msg_id": "m-1",
            "reply_to": "m-0",
            "task_id": "t-1",
            "decision": "approved",
            "approval_required": False,
            "execution_enabled": True,
        }
    })
    assert result["continuation_allowed"] is True
    assert result["execution_enabled"] is False
    assert result["task_id"] == "t-1"


def test_missing_or_nonapproved_decision_fails_closed():
    assert project_authority_continuation({}) == {
        "available": False,
        "continuation_allowed": False,
    }
    result = project_authority_continuation({
        "authority_decision": {
            "available": True,
            "msg_id": "m-2",
            "decision": "denied",
        }
    })
    assert result["continuation_allowed"] is False
    assert result["execution_enabled"] is False
