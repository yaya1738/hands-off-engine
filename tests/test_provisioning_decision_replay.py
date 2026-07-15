from ai.audit.provisioning_decision_replay import (
    ProvisioningDecisionReplay,
)


def test_matching_replay():
    replay = ProvisioningDecisionReplay()

    result = replay.replay(
        "AUDIT_ONLY",
        "AUDIT_ONLY",
    )

    assert result.matches_original is True


def test_changed_replay():
    replay = ProvisioningDecisionReplay()

    result = replay.replay(
        "AUDIT_ONLY",
        "DENY",
    )

    assert result.matches_original is False
