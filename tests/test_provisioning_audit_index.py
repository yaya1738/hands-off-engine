from ai.audit.provisioning_audit_index import (
    ProvisioningAuditIndex,
)
from ai.audit.provisioning_decision_record import (
    create_decision_record,
)


def make_record(request_id, decision, version):
    return create_decision_record(
        "decision-" + request_id,
        request_id,
        "agent",
        10,
        decision,
        "reason",
        "policy",
        version,
        "hash",
        {},
        True,
    )


def test_query_by_request():
    index = ProvisioningAuditIndex()

    index.add(make_record("req-1", "AUDIT_ONLY", "v1"))

    result = index.get_by_request_id("req-1")

    assert len(result) == 1
    assert result[0].request_id == "req-1"


def test_query_by_decision():
    index = ProvisioningAuditIndex()

    index.add(make_record("req-1", "DENY", "v1"))

    assert len(index.get_by_decision("DENY")) == 1


def test_query_by_policy_version():
    index = ProvisioningAuditIndex()

    index.add(make_record("req-1", "AUDIT_ONLY", "v2"))

    assert len(index.get_by_policy_version("v2")) == 1
