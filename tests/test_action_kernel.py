from ai.decision.action_kernel import decide


def test_complete_action_decision_passes_and_recomputes_costs():
    result = decide(
        action="bounded-test-action",
        confidence=0.9,
        risk_score=0.1,
        costs={"fee": 0.10, "slippage": 0.05},
        evidence={"probability": 0.9, "analysis_count": 3},
        risk_check=lambda: True,
    )
    assert result.approved is True
    assert result.total_cost == 0.15
    assert "cost-ledger-1" in result.checks
    assert "cost-ledger-2" in result.checks
    assert "risk-rule" in result.checks


def test_missing_evidence_blocks():
    result = decide(
        action="test",
        confidence=0.9,
        risk_score=0.1,
        costs={"fee": 0.1},
        evidence={},
    )
    assert result.approved is False


def test_missing_costs_block():
    result = decide(
        action="test",
        confidence=0.9,
        risk_score=0.1,
        costs={},
        evidence={"analysis": "present"},
    )
    assert result.approved is False


def test_failed_risk_check_blocks():
    result = decide(
        action="test",
        confidence=0.9,
        risk_score=0.1,
        costs={"fee": 0.1},
        evidence={"analysis": "present"},
        risk_check=lambda: False,
    )
    assert result.approved is False
