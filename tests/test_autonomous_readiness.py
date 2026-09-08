from tools.factory_forensics.autonomous_readiness import evaluate_checks


def test_autonomous_readiness_requires_full_independent_quorum():
    checks = [
        {"name": "Deployment Preflight", "bucket": "pass"},
        {"name": "Secret Scan", "bucket": "pass"},
        {"name": "Factory Authority Regression", "bucket": "pass"},
        {"name": "Autonomous Objective Cycle", "bucket": "pass"},
        {"name": "auto-merge", "bucket": "pending"},
    ]

    result = evaluate_checks(checks)

    assert result["ready"] is True
    assert result["missing_checks"] == []
    assert result["failing_checks"] == []


def test_autonomous_readiness_fails_closed_on_missing_or_nonpassing_evidence():
    result = evaluate_checks(
        [
            {"name": "Deployment Preflight", "bucket": "pass"},
            {"name": "Secret Scan", "bucket": "pass"},
            {"name": "Factory Authority Regression", "bucket": "pending"},
        ]
    )

    assert result["ready"] is False
    assert result["missing_checks"] == ["Autonomous Objective Cycle"]
    assert result["failing_checks"] == ["Factory Authority Regression"]
