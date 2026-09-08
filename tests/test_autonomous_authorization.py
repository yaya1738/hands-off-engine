from tools.factory_forensics.autonomous_authorization import evaluate_authorization


def test_authorized_envelope_is_deterministic_and_permitted():
    envelope = evaluate_authorization(
        actor="github-actions[bot]",
        branch="autonomous-factory/improve-runtime",
        paths=["ai/factory/example.py", "tests/test_example.py"],
        additions=120,
        deletions=30,
        readiness="pass",
    )
    assert envelope.permitted is True
    assert envelope.policy_version == "dass-preauthorization-v1"
    assert len(envelope.policy_hash) == 64
    assert envelope.reasons == ()


def test_human_actor_cannot_consume_autonomous_preauthorization():
    envelope = evaluate_authorization(
        actor="yaya1738",
        branch="autonomous-factory/improve-runtime",
        paths=["ai/factory/example.py"],
        readiness="pass",
    )
    assert envelope.permitted is False
    assert any("actor" in reason for reason in envelope.reasons)


def test_wrong_namespace_or_missing_readiness_fails_closed():
    envelope = evaluate_authorization(
        actor="github-actions[bot]",
        branch="feature/improve-runtime",
        paths=["ai/factory/example.py"],
        readiness="missing",
    )
    assert envelope.permitted is False
    assert any("namespace" in reason for reason in envelope.reasons)
    assert any("readiness" in reason for reason in envelope.reasons)


def test_protected_change_cannot_become_authorized_even_when_ready():
    envelope = evaluate_authorization(
        actor="github-actions[bot]",
        branch="autonomous-factory/improve-runtime",
        paths=[".github/workflows/production-deploy.yml"],
        readiness="pass",
    )
    assert envelope.permitted is False
    assert any("protected" in reason for reason in envelope.reasons)
