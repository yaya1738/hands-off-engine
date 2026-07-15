from ai.audit.provisioning_audit_lifecycle import (
    ProvisioningAuditLifecycle,
)


def test_audit_lifecycle_annotation_validates():
    lifecycle = ProvisioningAuditLifecycle()

    event = lifecycle.annotate(
        {"decision": "AUDIT_ONLY"},
        "v1",
        "standard",
    )

    result = lifecycle.validate_schema(event)

    assert result.valid is True
    assert result.schema_version == "v1"
    assert result.retention_class == "standard"


def test_missing_metadata_fails():
    lifecycle = ProvisioningAuditLifecycle()

    result = lifecycle.validate_schema({})

    assert result.valid is False
    assert "missing_schema_version" in result.issues
    assert "missing_retention_class" in result.issues
