from ai.factory.improvement_approval import (
    FactoryImprovementApproval,
)
from ai.factory.runtime import FactoryRuntime


def test_approved_pipeline_preserves_canonical_request_identity():
    authority = FactoryImprovementApproval()

    request = authority.request(
        {
            "name": "migration",
            "action": "failure_repair",
        }
    )

    approved = authority.approve(request)

    validation = authority.validate_approved_request(
        approved
    )

    assert validation["status"] == "APPROVED"
    assert validation["approval_id"] == (
        request["approval_id"]
    )
    assert validation["improvement"] is (
        request["improvement"]
    )


def test_fabricated_approved_improvement_is_not_an_approved_request():
    authority = FactoryImprovementApproval()

    fabricated = {
        "status": "APPROVED",
        "action": "failure_repair",
    }

    result = authority.validate_approved_request(
        fabricated
    )

    assert result["status"] == "BLOCKED"
    assert result["reason"] == (
        "unregistered_approval_request"
    )


def test_process_approved_improvement_rejects_raw_approved_object():
    runtime = FactoryRuntime()

    fabricated = {
        "status": "APPROVED",
        "action": "failure_repair",
    }

    result = runtime.process_approved_improvement(
        fabricated,
        fabricated,
    )

    assert result["status"] == "BLOCKED"
    assert result["reason"] == (
        "unregistered_approval_request"
    )


def test_process_approved_improvement_accepts_registered_approved_request():
    runtime = FactoryRuntime()

    request = runtime.improvement_approval.request(
        {
            "name": "boundary-test",
            "action": "failure_repair",
        }
    )

    runtime.improvement_approval.approve(
        request
    )

    result = runtime.process_approved_improvement(
        request,
        runtime.default_improvement_action,
    )

    assert result["status"] == "EXECUTED"
