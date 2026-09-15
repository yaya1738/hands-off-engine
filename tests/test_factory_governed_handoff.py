from scripts.factory_governed_handoff import build_governed_handoff


def test_handoff_preserves_proposal_and_cannot_enable_execution():
    result = build_governed_handoff({
        "available": True,
        "proposal": {
            "kind": "factory_improvement_proposal",
            "diagnosis": "interaction_degradation",
            "objective": "improve interaction reliability",
            "observation_complete": True,
            "requires_governance": True,
            "execution_enabled": True,
        },
    })
    handoff = result["handoff"]
    assert handoff["objective"] == "improve interaction reliability"
    assert handoff["requires_governance"] is True
    assert handoff["execution_enabled"] is False


def test_missing_governance_requirement_fails_closed():
    assert build_governed_handoff({
        "available": True,
        "proposal": {"kind": "factory_improvement_proposal"},
    }) == {"available": False}


def test_missing_proposal_fails_closed():
    assert build_governed_handoff(None) == {"available": False}
