#!/usr/bin/env python3
"""
Unit tests for Fed Rate Analyzer and Backtester
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alpha.fed_rate_analyzer import (
    FedRateAnalyzer,
    FedRateScenario,
    FedMeetingAnalysis,
    analyze_december_fomc,
)
from alpha.fed_rate_backtester import (
    FedRateBacktester,
    FOMCDecision,
    BacktestTrade,
)


class TestFedRateScenario:
    """Test FedRateScenario dataclass"""

    def test_scenario_creation(self):
        """Test creating a FedRateScenario"""
        scenario = FedRateScenario(
            target_rate_bps=425,
            description="25bps cut",
            fair_probability=0.65
        )
        assert scenario.target_rate_bps == 425
        assert scenario.description == "25bps cut"
        assert scenario.fair_probability == 0.65
        assert scenario.market_probability is None

    def test_scenario_with_market_probability(self):
        """Test scenario with market probability"""
        scenario = FedRateScenario(
            target_rate_bps=425,
            description="25bps cut",
            fair_probability=0.65,
            market_probability=0.55
        )
        assert scenario.market_probability == 0.55


class TestFedRateAnalyzer:
    """Test FedRateAnalyzer class"""

    def test_analyzer_initialization(self):
        """Test analyzer can be initialized"""
        analyzer = FedRateAnalyzer()
        assert analyzer.CURRENT_TARGET_RATE_BPS == 450
        assert analyzer.RATE_MOVE_BPS == 25

    def test_estimate_fair_probabilities_default(self):
        """Test fair probability estimation without futures data"""
        analyzer = FedRateAnalyzer()
        scenarios = analyzer.estimate_fair_probabilities()

        assert len(scenarios) == 3
        assert sum(s.fair_probability for s in scenarios) == pytest.approx(1.0, rel=0.01)

        # Check scenario types exist
        descriptions = [s.description for s in scenarios]
        assert "25bps cut" in descriptions
        assert "hold" in descriptions
        assert "50bps cut" in descriptions

    def test_estimate_fair_probabilities_with_futures(self):
        """Test fair probability estimation with futures data"""
        analyzer = FedRateAnalyzer()
        futures_data = {"price": 95.50}  # Implies 4.5% rate
        scenarios = analyzer.estimate_fair_probabilities(fed_futures_data=futures_data)

        assert len(scenarios) == 3
        # Probabilities should still sum to ~1.0
        total_prob = sum(s.fair_probability for s in scenarios)
        assert 0.99 <= total_prob <= 1.01

    def test_fetch_polymarket_odds_default(self):
        """Test fetching Polymarket odds without data"""
        analyzer = FedRateAnalyzer()
        odds = analyzer.fetch_polymarket_odds()

        assert "25bps cut" in odds
        assert "hold" in odds
        assert "50bps cut" in odds
        assert all(0 <= v <= 1 for v in odds.values())

    def test_fetch_polymarket_odds_with_data(self):
        """Test fetching Polymarket odds with provided data"""
        analyzer = FedRateAnalyzer()
        data = {
            "25bps_cut": 0.60,
            "hold": 0.25,
            "50bps_cut": 0.15
        }
        odds = analyzer.fetch_polymarket_odds(polymarket_data=data)

        assert odds["25bps cut"] == 0.60
        assert odds["hold"] == 0.25
        assert odds["50bps cut"] == 0.15

    def test_calculate_edge_positive(self):
        """Test edge calculation when fair > market"""
        analyzer = FedRateAnalyzer()
        edge, side = analyzer.calculate_edge(fair_prob=0.70, market_prob=0.50)

        assert edge == pytest.approx(0.20)
        assert side == "YES"

    def test_calculate_edge_negative(self):
        """Test edge calculation when fair < market"""
        analyzer = FedRateAnalyzer()
        edge, side = analyzer.calculate_edge(fair_prob=0.30, market_prob=0.50)

        assert edge == pytest.approx(0.20)
        assert side == "NO"

    def test_calculate_confidence_low_edge(self):
        """Test confidence calculation with low edge"""
        analyzer = FedRateAnalyzer()
        confidence = analyzer.calculate_confidence(edge=0.03)

        # Low edge should result in base confidence (0.7) unmodified
        # as edge < 0.05 doesn't trigger any reduction multipliers
        assert 0.6 <= confidence <= 0.8

    def test_calculate_confidence_high_edge(self):
        """Test confidence calculation with high edge"""
        analyzer = FedRateAnalyzer()
        confidence = analyzer.calculate_confidence(edge=0.20)

        # High edge (> 0.15) multiplies base confidence by 0.5
        # Base 0.7 * 0.5 = 0.35, so confidence should be low
        assert confidence < 0.6

    def test_calculate_confidence_high_liquidity(self):
        """Test confidence adjustment for high liquidity"""
        analyzer = FedRateAnalyzer()
        conf_low = analyzer.calculate_confidence(edge=0.05, liquidity=1_000_000)
        conf_high = analyzer.calculate_confidence(edge=0.05, liquidity=200_000_000)

        # Higher liquidity should slightly reduce confidence (market is efficient)
        assert conf_high < conf_low

    def test_analyze_fed_meeting(self):
        """Test full meeting analysis"""
        analyzer = FedRateAnalyzer()
        analysis = analyzer.analyze_fed_meeting(
            meeting_date="2025-12-17",
            market_volume_usd=159_000_000.0
        )

        assert isinstance(analysis, FedMeetingAnalysis)
        assert analysis.meeting_date == "2025-12-17"
        assert analysis.current_rate_bps == 450
        assert len(analysis.scenarios) == 3
        assert 0 <= analysis.edge <= 1
        assert 0 <= analysis.confidence <= 1

    def test_generate_alpha_signals(self):
        """Test alpha signal generation"""
        analyzer = FedRateAnalyzer()
        analysis = analyzer.analyze_fed_meeting()
        signals = analyzer.generate_alpha_signals(analysis, min_edge=0.05)

        # Should have at least one signal if edge exists
        assert isinstance(signals, list)

        if signals:
            signal = signals[0]
            assert "market_id" in signal
            assert "question" in signal
            assert "side" in signal
            assert "model_edge" in signal
            assert "model_confidence" in signal
            assert "fair_price" in signal
            assert "market_price" in signal
            assert signal["query_category"] == "fed_rate"

    def test_generate_alpha_signals_min_edge_filter(self):
        """Test that min_edge filter works"""
        analyzer = FedRateAnalyzer()
        analysis = analyzer.analyze_fed_meeting()

        # High min_edge should filter out more signals
        signals_low = analyzer.generate_alpha_signals(analysis, min_edge=0.01)
        signals_high = analyzer.generate_alpha_signals(analysis, min_edge=0.50)

        assert len(signals_high) <= len(signals_low)


class TestAnalyzeDecemberFOMC:
    """Test the analyze_december_fomc convenience function"""

    def test_analyze_december_fomc_basic(self):
        """Test basic December FOMC analysis"""
        result = analyze_december_fomc()

        assert "generated_at" in result
        assert result["analysis_type"] == "fed_rate"
        assert result["meeting_date"] == "2025-12-17"
        assert "recommendation" in result
        assert "edge" in result
        assert "confidence" in result
        assert "scenarios" in result
        assert "alpha_signals" in result

    def test_analyze_december_fomc_with_output(self):
        """Test analysis with file output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fed_analysis.json"
            result = analyze_december_fomc(output_path=output_path)

            assert output_path.exists()

            with open(output_path) as f:
                saved = json.load(f)

            assert saved["meeting_date"] == result["meeting_date"]
            assert saved["edge"] == result["edge"]


class TestFedRateBacktester:
    """Test FedRateBacktester class"""

    def test_backtester_initialization(self):
        """Test backtester can be initialized"""
        backtester = FedRateBacktester()
        assert len(backtester.historical_decisions) > 0

    def test_normalize_outcome_cut(self):
        """Test outcome normalization for cuts"""
        backtester = FedRateBacktester()

        assert backtester.normalize_outcome("25bps cut") == "25bps cut"
        assert backtester.normalize_outcome("50bps Cut") == "50bps cut"
        assert backtester.normalize_outcome("CUT") == "cut"

    def test_normalize_outcome_hike(self):
        """Test outcome normalization for hikes"""
        backtester = FedRateBacktester()

        assert backtester.normalize_outcome("25bps hike") == "25bps hike"
        assert backtester.normalize_outcome("75bps HIKE") == "75bps hike"

    def test_normalize_outcome_hold(self):
        """Test outcome normalization for holds"""
        backtester = FedRateBacktester()

        assert backtester.normalize_outcome("hold") == "hold"
        assert backtester.normalize_outcome("HOLD") == "hold"
        assert backtester.normalize_outcome("unchanged") == "hold"

    def test_evaluate_trade_correct_yes(self):
        """Test trade evaluation when YES prediction is correct"""
        backtester = FedRateBacktester()
        trade = backtester.evaluate_trade(
            predicted="25bps cut",
            actual="25bps cut",
            side="YES",
            entry_price=0.50
        )

        assert trade.was_correct is True
        assert trade.exit_price == 1.0
        assert trade.pnl == 0.50

    def test_evaluate_trade_incorrect_yes(self):
        """Test trade evaluation when YES prediction is wrong"""
        backtester = FedRateBacktester()
        trade = backtester.evaluate_trade(
            predicted="25bps cut",
            actual="hold",
            side="YES",
            entry_price=0.50
        )

        assert trade.was_correct is False
        assert trade.exit_price == 0.0
        assert trade.pnl == -0.50

    def test_evaluate_trade_correct_no(self):
        """Test trade evaluation when NO prediction is correct"""
        backtester = FedRateBacktester()
        trade = backtester.evaluate_trade(
            predicted="25bps cut",
            actual="hold",
            side="NO",
            entry_price=0.50
        )

        assert trade.was_correct is True
        assert trade.pnl == 0.50

    def test_run_backtest_basic(self):
        """Test running a basic backtest"""
        backtester = FedRateBacktester()
        model_prices = {
            "25bps cut": 0.50,
            "hold": 0.30,
            "25bps hike": 0.50,
        }
        result = backtester.run_backtest(model_prices)

        assert result.total_trades > 0
        assert result.winning_trades >= 0
        assert result.losing_trades >= 0
        assert result.winning_trades + result.losing_trades == result.total_trades
        assert 0 <= result.hit_rate <= 1

    def test_run_backtest_date_filter(self):
        """Test backtest with date filtering"""
        backtester = FedRateBacktester()
        model_prices = {"25bps cut": 0.50}

        # Full range
        full_result = backtester.run_backtest(model_prices)

        # Filtered range
        filtered_result = backtester.run_backtest(
            model_prices,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        assert filtered_result.total_trades <= full_result.total_trades

    def test_run_backtest_empty(self):
        """Test backtest with no matching trades"""
        backtester = FedRateBacktester()
        result = backtester.run_backtest(
            model_fair_prices={"25bps cut": 0.50},
            start_date="2030-01-01"  # Future date, no trades
        )

        assert result.total_trades == 0
        assert result.hit_rate == 0.0
        assert result.total_pnl == 0.0

    def test_generate_report(self):
        """Test report generation"""
        backtester = FedRateBacktester()
        result = backtester.run_backtest({"25bps cut": 0.50})
        report = backtester.generate_report(result)

        assert "FED RATE BACKTEST REPORT" in report
        assert "Hit Rate:" in report
        assert "Total P&L:" in report


class TestFOMCDecision:
    """Test FOMCDecision dataclass"""

    def test_fomc_decision_creation(self):
        """Test creating an FOMCDecision"""
        decision = FOMCDecision(
            meeting_date="2024-12-18",
            rate_before_bps=450,
            rate_after_bps=425,
            decision="25bps cut",
            change_bps=-25
        )
        assert decision.meeting_date == "2024-12-18"
        assert decision.rate_before_bps == 450
        assert decision.rate_after_bps == 425
        assert decision.decision == "25bps cut"
        assert decision.change_bps == -25


class TestIntegration:
    """Integration tests for the full Fed rate analysis pipeline"""

    def test_analyzer_to_model_format(self):
        """Test that analyzer output can be consumed by Decider"""
        analyzer = FedRateAnalyzer()
        analysis = analyzer.analyze_fed_meeting()
        signals = analyzer.generate_alpha_signals(analysis)

        # Verify signals match expected model format
        for signal in signals:
            # Required fields from polymarket-model.json format
            assert "market_id" in signal
            assert "question" in signal
            assert "side" in signal
            assert "model_edge" in signal
            assert "model_confidence" in signal
            assert "fair_price" in signal
            assert "market_price" in signal

            # Verify value ranges
            assert 0 <= signal["model_edge"] <= 1
            assert 0 <= signal["model_confidence"] <= 1
            assert signal["side"] in ["YES", "NO"]

    def test_backtest_with_analysis_output(self):
        """Test that backtest can use analysis output"""
        # Generate analysis
        analyzer = FedRateAnalyzer()
        scenarios = analyzer.estimate_fair_probabilities()

        # Convert to backtest format
        model_prices = {
            s.description: s.fair_probability
            for s in scenarios
        }

        # Run backtest
        backtester = FedRateBacktester()
        result = backtester.run_backtest(model_prices)

        # Should complete without errors
        assert result.total_trades > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
