from ai.factory.improvement_approval import (
    FactoryImprovementApproval,
)


def test_request():
    workflow = FactoryImprovementApproval()

    result = workflow.request(
        {
            "name": "migration",
        }
    )

    assert result["status"] == "PENDING"


def test_approve():
    workflow = FactoryImprovementApproval()

    request = workflow.request(
        {
            "name": "change",
        }
    )

    result = workflow.approve(
        request
    )

    assert result["status"] == "APPROVED"


def test_reject():
    workflow = FactoryImprovementApproval()

    request = workflow.request(
        {
            "name": "change",
        }
    )

    result = workflow.reject(
        request
    )

    assert result["status"] == "REJECTED"


def test_history():
    workflow = FactoryImprovementApproval()

    workflow.request(
        {
            "name": "test",
        }
    )

    assert len(workflow.history()) == 1
