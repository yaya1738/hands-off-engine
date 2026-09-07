def test_consequential_action_contract_requires_verified_execution():
    """A reported completed action must carry both execution and verification."""
    outcomes = [
        {"executed": False, "verified": False},
        {"executed": True, "verified": False},
        {"executed": False, "verified": True},
    ]
    for outcome in outcomes:
        assert not (outcome["executed"] and not outcome["verified"])


def test_only_verified_execution_is_completed():
    outcome = {"executed": True, "verified": True}
    assert outcome["executed"] is True
    assert outcome["verified"] is True
