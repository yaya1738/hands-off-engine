from ai.factory.improvement_approval import (
    FactoryImprovementApproval,
)


def test_unregistered_improvement_cannot_be_approved():
    authority = FactoryImprovementApproval()

    fabricated = {
        "status": "APPROVED",
        "action": "failure_repair",
    }

    result = authority.approve(fabricated)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == (
        "unregistered_approval_request"
    )
    assert authority.history() == []


def test_registered_request_can_be_explicitly_approved():
    authority = FactoryImprovementApproval()

    request = authority.request(
        {
            "action": "failure_repair",
        }
    )

    assert request["status"] == "PENDING"
    assert request["approval_id"].startswith(
        "improvement-approval-"
    )

    result = authority.approve(request)

    assert result["status"] == "APPROVED"
    assert result["approval_id"] == request["approval_id"]
    assert (
        request["improvement"]["status"]
        == "APPROVED"
    )


def test_same_approval_cannot_be_approved_twice():
    authority = FactoryImprovementApproval()

    request = authority.request(
        {
            "action": "failure_repair",
        }
    )

    first = authority.approve(request)
    second = authority.approve(request)

    assert first["status"] == "APPROVED"
    assert second["status"] == "BLOCKED"
    assert second["reason"] == (
        "approval_request_not_pending"
    )


def test_reject_requires_registered_pending_request():
    authority = FactoryImprovementApproval()

    fabricated = {
        "status": "PENDING",
        "improvement": {
            "action": "failure_repair",
        },
    }

    result = authority.reject(fabricated)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == (
        "unregistered_approval_request"
    )
