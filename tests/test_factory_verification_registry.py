from ai.factory.verification_registry import (
    FactoryVerificationRegistry,
)


def test_record_verification():
    registry = FactoryVerificationRegistry()

    registry.record_verification(
        "verify-001",
        "artifact-001",
        "PASS",
        {
            "tests": 3,
        },
    )

    result = registry.get_verification(
        "verify-001"
    )

    assert result["status"] == "PASS"
    assert result["details"]["tests"] == 3


def test_find_by_artifact():
    registry = FactoryVerificationRegistry()

    registry.record_verification(
        "verify-002",
        "artifact-002",
        "FAIL",
    )

    results = registry.find_by_artifact(
        "artifact-002"
    )

    assert len(results) == 1
    assert results[0]["status"] == "FAIL"


def test_empty_registry():
    registry = FactoryVerificationRegistry()

    assert registry.list_verifications() == []
