from autonomous.credentials.intelligence.decision_gate import (
    IntelligenceDecisionGate,
)


def test_gate():

    result = IntelligenceDecisionGate().evaluate(
        0.69,
        "degraded",
        "declining",
        "moderate",
    )

    assert result["gate_status"] == "human_review_recommended"
    assert result["mode"] == "read_only"
