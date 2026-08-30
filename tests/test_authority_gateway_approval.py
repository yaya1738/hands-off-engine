from ai.factory.authority_gateway import FactoryAuthorityGateway


class _FakeApproval:
    def __init__(self):
        self.calls = []

    def approve(self, request):
        self.calls.append(("approve", request))
        return {"status": "APPROVED", "approval_id": request["approval_id"]}

    def reject(self, request):
        self.calls.append(("reject", request))
        return {"status": "REJECTED", "approval_id": request["approval_id"]}

    def validate_approved_request(self, request):
        self.calls.append(("validate", request))
        return {"status": "APPROVED", "approval_id": request["approval_id"]}


def _gateway_with_fake_approval():
    gateway = object.__new__(FactoryAuthorityGateway)
    gateway.approval = _FakeApproval()
    return gateway


def test_approve_improvement_delegates_to_authority_approval():
    gateway = _gateway_with_fake_approval()
    request = {"approval_id": "approval-1"}

    result = gateway.approve_improvement(request)

    assert result == {"status": "APPROVED", "approval_id": "approval-1"}
    assert gateway.approval.calls == [("approve", request)]


def test_reject_improvement_delegates_to_authority_approval():
    gateway = _gateway_with_fake_approval()
    request = {"approval_id": "approval-2"}

    result = gateway.reject_improvement(request)

    assert result == {"status": "REJECTED", "approval_id": "approval-2"}
    assert gateway.approval.calls == [("reject", request)]


def test_validate_approved_improvement_does_not_execute():
    gateway = _gateway_with_fake_approval()
    request = {"approval_id": "approval-3"}

    result = gateway.validate_approved_improvement(request)

    assert result == {"status": "APPROVED", "approval_id": "approval-3"}
    assert gateway.approval.calls == [("validate", request)]
