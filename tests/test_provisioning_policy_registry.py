from ai.audit.provisioning_policy_registry import (
    ProvisioningPolicyRegistry,
)


def test_policy_registration_creates_hash():
    registry = ProvisioningPolicyRegistry()

    result = registry.register(
        "cost-policy",
        "v1",
        {"max_allowed_cost": 1000},
    )

    assert result.policy_id == "cost-policy"
    assert result.version == "v1"
    assert result.policy_hash
