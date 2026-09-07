from trading.action_calculation_gateway import evaluate_action


def analysis(probability, confidence="high"):
    return {
        "fair_probability": probability,
        "confidence": confidence,
        "reasoning": "independent analysis",
    }


def costs(**overrides):
    value = {
        "exchange_fees_usd": 0.01,
        "slippage_usd": 0.01,
        "spread_cost_usd": 0.01,
        "network_fees_usd": 0.01,
        "funding_or_financing_usd": 0.01,
        "other_known_costs_usd": 0.01,
    }
    value.update(overrides)
    return value


def test_complete_brain_and_cost_evidence_can_approve():
    result = evaluate_action(
        trade_size_usd=2,
        market_price=0.40,
        analyses=[analysis(0.80), analysis(0.80)],
        costs=costs(),
        expected_payout_multiple=2,
        brain_evidence={"source": "integrated-brain", "confidence": 0.8},
    )
    assert result.approved
    assert result.total_cost == 0.06
    assert result.decision.approved


def test_missing_expense_category_fails_closed():
    evidence = costs()
    del evidence["slippage_usd"]
    result = evaluate_action(
        trade_size_usd=2,
        market_price=0.40,
        analyses=[analysis(0.80)],
        costs=evidence,
    )
    assert not result.approved
    assert "missing cost evidence" in result.reason


def test_all_expenses_are_double_counted_in_total_before_decision():
    evidence = costs(
        exchange_fees_usd=0.10,
        slippage_usd=0.20,
        spread_cost_usd=0.30,
        network_fees_usd=0.40,
        funding_or_financing_usd=0.50,
        other_known_costs_usd=0.60,
    )
    result = evaluate_action(
        trade_size_usd=2,
        market_price=0.40,
        analyses=[analysis(0.80), analysis(0.80)],
        costs=evidence,
        expected_payout_multiple=2,
    )
    assert result.total_cost == 2.10
    assert result.decision.total_cost == 2.10
    assert not result.approved
