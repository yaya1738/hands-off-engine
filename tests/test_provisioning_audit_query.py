from types import SimpleNamespace

from ai.audit.provisioning_audit_query import (
    ProvisioningAuditQuery,
)


def test_query_by_request_id():
    query = ProvisioningAuditQuery()

    query.add(
        SimpleNamespace(
            request_id="req-1",
            decision="AUDIT_ONLY",
            policy_version="v1",
        )
    )

    result = query.find_by_request_id("req-1")

    assert len(result) == 1


def test_query_by_decision():
    query = ProvisioningAuditQuery()

    query.add(
        SimpleNamespace(
            request_id="req-2",
            decision="DENY",
            policy_version="v1",
        )
    )

    result = query.find_by_decision("DENY")

    assert len(result) == 1
