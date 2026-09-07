from trading.decision_gate import evaluate_trade


class PassingSafeguards:
    def check_all_safeguards(self, trade_size_usd):
        return True, ["all safeguards passed"]


def analysis(probability, confidence="high"):
    return {
        "fair_probability": probability,
        "confidence": confidence,
        "reasoning": "independent market analysis",
    }


def test_positive_net_ev_requires_all_checks():
    result = evaluate_trade(
        trade_size_usd=2.0,
        market_price=0.40,
        analyses=[analysis(0.80), analysis(0.80)],
        explicit_costs_usd=0.05,
        expected_payout_multiple=2.0,
        safeguards=PassingSafeguards(),
    )
    assert result.approved is True
    assert result.total_cost == 0.05
    assert "probability-consensus-1" in result.checks
    assert "probability-consensus-2" in result.checks
    assert "economic-recomputation" in result.checks


def test_costs_can_turn_positive_gross_trade_into_rejection():
    result = evaluate_trade(
        trade_size_usd=2.0,
        market_price=0.80,
        analyses=[analysis(0.81)],
        explicit_costs_usd=0.10,
        expected_payout_multiple=1.0,
        safeguards=PassingSafeguards(),
    )
    assert result.approved is False
    assert "cost" in result.reason


def test_missing_analysis_fails_closed():
    result = evaluate_trade(
        trade_size_usd=2.0,
        market_price=0.40,
        analyses=[],
        safeguards=PassingSafeguards(),
    )
    assert result.approved is False
    assert "probability" in result.reason


def test_disagreement_defers_trade():
    result = evaluate_trade(
        trade_size_usd=2.0,
        market_price=0.40,
        analyses=[analysis(0.90), analysis(0.50)],
        safeguards=PassingSafeguards(),
    )
    assert result.approved is False
    assert "disagreement" in result.reason


def test_hard_position_limit_is_never_overridden():
    result = evaluate_trade(
        trade_size_usd=201.0,
        market_price=0.20,
        analyses=[analysis(0.95)],
        safeguards=PassingSafeguards(),
    )
    assert result.approved is False
    assert "absolute position" in result.reason
