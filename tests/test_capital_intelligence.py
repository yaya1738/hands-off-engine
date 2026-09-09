from ai.factory.capital_intelligence import CapitalIntelligence, CapitalOpportunity


def test_no_positive_edge_holds_cash():
    brain = CapitalIntelligence()
    opportunity = CapitalOpportunity(
        opportunity_id="bad",
        venue="polymarket",
        thesis="weak edge",
        expected_return=0.01,
        downside=1.0,
        probability=0.01,
        capital_required=1.0,
    )
    decision = brain.decide([opportunity], 10.0)
    assert decision["action"] == "hold_cash"
    assert decision["allocation"] == 0.0


def test_best_positive_opportunity_is_fractionally_sized():
    brain = CapitalIntelligence(max_fraction_per_opportunity=0.20)
    opportunity = CapitalOpportunity(
        opportunity_id="edge",
        venue="kalshi",
        thesis="strongly supported edge",
        expected_return=0.40,
        downside=0.05,
        probability=0.90,
        capital_required=9.0,
        liquidity=1.0,
    )
    decision = brain.decide([opportunity], 10.0)
    assert decision["action"] == "propose_allocation"
    assert decision["venue"] == "kalshi"
    assert decision["allocation"] == 2.0


def test_rebalance_only_proposes_transfer():
    brain = CapitalIntelligence()
    opportunity = CapitalOpportunity(
        opportunity_id="edge",
        venue="polymarket",
        thesis="positive expected value",
        expected_return=0.20,
        downside=0.01,
        probability=0.80,
        capital_required=1.0,
    )
    plan = brain.rebalance_plan({"cash": 10.0, "kalshi": 0.0, "polymarket": 0.0}, [opportunity])
    assert plan["transfers"][0]["status"] == "proposed"
    assert plan["execution_authority"] == "external_authorized_financial_adapter"
