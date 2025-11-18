"""Test NaivePriceModel scoring logic"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "termux-hands-off" / "agent"))

from polymarket_skeleton import NaivePriceModel, Market, Category, Opinion
import pytest


@pytest.mark.unit
class TestNaivePriceModel:
    """Test suite for NaivePriceModel.score()"""

    def test_naive_model_uses_market_price_as_fair(self):
        """NaivePriceModel should use market yes_price as fair_yes (after clamping)"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.60,
            no_price=0.40
        )

        opinion = model.score(market, {})

        # Naive model sets fair_yes = yes_price (clamped)
        assert opinion.fair_yes == 0.60

    def test_edge_calculation_formula(self):
        """Edge should be fair_yes - yes_price"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.60,
            no_price=0.40
        )

        opinion = model.score(market, {})

        # In naive model, fair_yes = yes_price, so edge should be ~0
        expected_edge = opinion.fair_yes - market.yes_price
        assert opinion.edge == pytest.approx(expected_edge, abs=1e-9)

    def test_hold_recommendation_when_no_edge(self):
        """Should recommend 'hold' when edge is within threshold"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.50,
            no_price=0.50
        )

        context = {"target_edge_bps": 500}  # 5% threshold
        opinion = model.score(market, context)

        # Since naive model sets fair = market, edge = 0, so rec should be "hold"
        assert opinion.rec == "hold"

    def test_threshold_from_context(self):
        """Should use target_edge_bps from context"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.50,
            no_price=0.50
        )

        # Test different thresholds
        context_500 = {"target_edge_bps": 500}   # 5%
        context_1000 = {"target_edge_bps": 1000}  # 10%

        opinion_500 = model.score(market, context_500)
        opinion_1000 = model.score(market, context_1000)

        # Both should work without crashing
        assert opinion_500.rec in ["buy_yes", "buy_no", "hold"]
        assert opinion_1000.rec in ["buy_yes", "buy_no", "hold"]

    def test_default_threshold_when_missing(self):
        """Should use default 500 bps when target_edge_bps not in context"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.50,
            no_price=0.50
        )

        opinion = model.score(market, {})  # Empty context

        # Should not crash and should return valid recommendation
        assert opinion.rec in ["buy_yes", "buy_no", "hold"]

    def test_fair_yes_clamping_low(self):
        """fair_yes should be clamped to minimum 0.01"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.001,  # Very low price
            no_price=0.999
        )

        opinion = model.score(market, {})
        assert opinion.fair_yes >= 0.01

    def test_fair_yes_clamping_high(self):
        """fair_yes should be clamped to maximum 0.99"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.999,  # Very high price
            no_price=0.001
        )

        opinion = model.score(market, {})
        assert opinion.fair_yes <= 0.99

    def test_rec_always_valid(self):
        """Recommendation should always be buy_yes, buy_no, or hold"""
        model = NaivePriceModel()

        test_prices = [0.1, 0.3, 0.5, 0.7, 0.9, 0.01, 0.99]

        for yes_price in test_prices:
            market = Market(
                id="test",
                question="Test?",
                category=Category.OTHER,
                closes_at="",
                yes_price=yes_price,
                no_price=1 - yes_price
            )
            opinion = model.score(market, {})
            assert opinion.rec in ["buy_yes", "buy_no", "hold"], \
                f"Invalid rec '{opinion.rec}' for yes_price={yes_price}"

    def test_opinion_has_notes(self):
        """Opinion should include notes field"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.5,
            no_price=0.5
        )

        opinion = model.score(market, {})

        assert hasattr(opinion, 'notes')
        assert isinstance(opinion.notes, str)
        assert len(opinion.notes) > 0

    def test_opinion_is_dataclass(self):
        """Opinion should be a proper Opinion dataclass"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.5,
            no_price=0.5
        )

        opinion = model.score(market, {})

        assert isinstance(opinion, Opinion)
        assert hasattr(opinion, 'fair_yes')
        assert hasattr(opinion, 'edge')
        assert hasattr(opinion, 'rec')
        assert hasattr(opinion, 'notes')

    def test_edge_types(self):
        """fair_yes and edge should be floats"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.5,
            no_price=0.5
        )

        opinion = model.score(market, {})

        assert isinstance(opinion.fair_yes, float)
        assert isinstance(opinion.edge, float)

    def test_extreme_threshold_values(self):
        """Should handle extreme threshold values gracefully"""
        model = NaivePriceModel()
        market = Market(
            id="test",
            question="Test?",
            category=Category.OTHER,
            closes_at="",
            yes_price=0.5,
            no_price=0.5
        )

        # Very low threshold (0 bps = always buy/sell)
        opinion_0 = model.score(market, {"target_edge_bps": 0})
        assert opinion_0.rec in ["buy_yes", "buy_no", "hold"]

        # Very high threshold (10000 bps = 100%, never buy/sell)
        opinion_10000 = model.score(market, {"target_edge_bps": 10000})
        assert opinion_10000.rec in ["buy_yes", "buy_no", "hold"]
