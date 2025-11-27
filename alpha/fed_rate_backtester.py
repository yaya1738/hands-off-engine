#!/usr/bin/env python3
"""
Fed Rate Backtester: Historical Performance Analysis
=====================================================

This module provides backtesting capabilities for Fed rate prediction models.
It analyzes historical FOMC decisions and evaluates model performance.

Key features:
- Load historical FOMC decision data
- Calculate hypothetical P&L from model predictions
- Compute accuracy metrics (hit rate, edge realization)
- Generate performance reports
"""

import json
import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class FOMCDecision:
    """Represents a historical FOMC rate decision"""
    meeting_date: str  # ISO date
    rate_before_bps: int  # Rate before decision in bps
    rate_after_bps: int  # Rate after decision in bps
    decision: str  # "hike", "cut", "hold", "25bps cut", etc.
    change_bps: int  # Change in basis points (negative for cuts)


@dataclass
class BacktestTrade:
    """Represents a hypothetical trade in backtest"""
    meeting_date: str
    predicted_outcome: str
    actual_outcome: str
    side: str  # "YES" or "NO"
    entry_price: float  # Price we would have paid
    exit_price: float  # 1.0 if correct, 0.0 if wrong
    pnl: float  # Profit/loss on a $1 bet
    was_correct: bool


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    start_date: str
    end_date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    hit_rate: float  # Percentage of correct predictions
    average_edge: float  # Average edge per trade
    sharpe_ratio: Optional[float] = None
    trades: Optional[List[BacktestTrade]] = None


# Historical FOMC decisions (2022-2024 sample data)
# In production, this would be fetched from a data source
HISTORICAL_FOMC_DECISIONS = [
    FOMCDecision("2024-09-18", 550, 500, "50bps cut", -50),
    FOMCDecision("2024-07-31", 550, 550, "hold", 0),
    FOMCDecision("2024-06-12", 550, 550, "hold", 0),
    FOMCDecision("2024-05-01", 550, 550, "hold", 0),
    FOMCDecision("2024-03-20", 550, 550, "hold", 0),
    FOMCDecision("2024-01-31", 550, 550, "hold", 0),
    FOMCDecision("2023-12-13", 550, 550, "hold", 0),
    FOMCDecision("2023-11-01", 550, 550, "hold", 0),
    FOMCDecision("2023-09-20", 550, 550, "hold", 0),
    FOMCDecision("2023-07-26", 525, 550, "25bps hike", 25),
    FOMCDecision("2023-06-14", 525, 525, "hold", 0),
    FOMCDecision("2023-05-03", 500, 525, "25bps hike", 25),
    FOMCDecision("2023-03-22", 475, 500, "25bps hike", 25),
    FOMCDecision("2023-02-01", 450, 475, "25bps hike", 25),
    FOMCDecision("2022-12-14", 425, 450, "25bps hike", 25),
    FOMCDecision("2022-11-02", 375, 400, "75bps hike", 75),
    FOMCDecision("2022-09-21", 300, 325, "75bps hike", 75),
    FOMCDecision("2022-07-27", 225, 250, "75bps hike", 75),
    FOMCDecision("2022-06-15", 150, 175, "75bps hike", 75),
    FOMCDecision("2022-05-04", 75, 100, "50bps hike", 50),
    FOMCDecision("2022-03-16", 25, 50, "25bps hike", 25),
]


class FedRateBacktester:
    """
    Backtester for Fed rate prediction models.

    Simulates trading based on model predictions against
    historical FOMC decisions.
    """

    def __init__(self):
        """Initialize the backtester"""
        self.audit = get_audit_logger(component="alpha.fed_rate_backtest")
        self.historical_decisions = HISTORICAL_FOMC_DECISIONS

    def normalize_outcome(self, decision: Optional[str]) -> str:
        """Normalize decision string to comparable format"""
        if decision is None:
            return "unknown"
        decision = decision.lower().strip()
        if "cut" in decision:
            if "50" in decision:
                return "50bps cut"
            elif "25" in decision:
                return "25bps cut"
            return "cut"
        elif "hike" in decision:
            if "75" in decision:
                return "75bps hike"
            elif "50" in decision:
                return "50bps hike"
            elif "25" in decision:
                return "25bps hike"
            return "hike"
        else:
            return "hold"

    def simulate_prediction(
        self,
        meeting: FOMCDecision,
        model_fair_prices: Dict[str, float]
    ) -> Tuple[Optional[str], float, str]:
        """
        Simulate what our model would have predicted.

        For backtesting, we use the model's fair prices to determine
        which outcome we would have bet on.

        Args:
            meeting: The FOMC meeting to simulate
            model_fair_prices: Dict of outcome -> fair probability

        Returns:
            Tuple of (predicted_outcome, entry_price, side)
        """
        # Find the outcome where we have the largest edge
        best_outcome: Optional[str] = None
        best_edge = 0.0

        # Simulate what market prices might have been
        # (In production, use actual historical market data)
        market_prices = {
            "25bps cut": 0.50,
            "50bps cut": 0.10,
            "hold": 0.30,
            "25bps hike": 0.50,
            "50bps hike": 0.10,
            "75bps hike": 0.05,
        }

        for outcome, fair_price in model_fair_prices.items():
            market_price = market_prices.get(outcome, 0.50)
            edge = fair_price - market_price

            if abs(edge) > abs(best_edge):
                best_edge = edge
                best_outcome = outcome

        # Handle case where no outcome is found
        if best_outcome is None:
            # Default to most common outcome
            best_outcome = "hold"
            best_edge = 0.0

        # Determine side based on edge direction
        if best_edge > 0:
            side = "YES"
            entry_price = market_prices.get(best_outcome, 0.50)
        else:
            side = "NO"
            entry_price = 1 - market_prices.get(best_outcome, 0.50)

        return best_outcome, entry_price, side

    def evaluate_trade(
        self,
        predicted: str,
        actual: str,
        side: str,
        entry_price: float
    ) -> BacktestTrade:
        """
        Evaluate a single trade against the actual outcome.

        Args:
            predicted: What we predicted
            actual: What actually happened
            side: "YES" or "NO"
            entry_price: Price we paid

        Returns:
            BacktestTrade with P&L calculation
        """
        predicted_norm = self.normalize_outcome(predicted)
        actual_norm = self.normalize_outcome(actual)

        # Determine if prediction was correct
        if side == "YES":
            was_correct = predicted_norm == actual_norm
        else:
            was_correct = predicted_norm != actual_norm

        # Calculate P&L
        if was_correct:
            exit_price = 1.0
            pnl = exit_price - entry_price
        else:
            exit_price = 0.0
            pnl = -entry_price

        return BacktestTrade(
            meeting_date="",  # Will be set by caller
            predicted_outcome=predicted,
            actual_outcome=actual,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            was_correct=was_correct
        )

    def run_backtest(
        self,
        model_fair_prices: Dict[str, float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """
        Run a full backtest using the model's fair prices.

        Args:
            model_fair_prices: Dict mapping outcomes to fair probabilities
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            BacktestResult with performance metrics
        """
        trades = []

        for meeting in self.historical_decisions:
            # Apply date filters
            if start_date and meeting.meeting_date < start_date:
                continue
            if end_date and meeting.meeting_date > end_date:
                continue

            # Simulate what we would have predicted
            predicted, entry_price, side = self.simulate_prediction(
                meeting, model_fair_prices
            )

            # Evaluate the trade
            trade = self.evaluate_trade(
                predicted=predicted,
                actual=meeting.decision,
                side=side,
                entry_price=entry_price
            )
            trade.meeting_date = meeting.meeting_date
            trades.append(trade)

        # Calculate aggregate metrics
        if not trades:
            return BacktestResult(
                start_date=start_date or "",
                end_date=end_date or "",
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_pnl=0.0,
                hit_rate=0.0,
                average_edge=0.0,
                trades=[]
            )

        winning_trades = sum(1 for t in trades if t.was_correct)
        losing_trades = len(trades) - winning_trades
        total_pnl = sum(t.pnl for t in trades)
        hit_rate = winning_trades / len(trades) if trades else 0.0

        # Calculate average edge (realized)
        average_edge = total_pnl / len(trades) if trades else 0.0

        # Calculate Sharpe ratio (simplified)
        if len(trades) > 1:
            pnls = [t.pnl for t in trades]
            mean_pnl = sum(pnls) / len(pnls)
            variance = sum((p - mean_pnl) ** 2 for p in pnls) / len(pnls)
            std_pnl = variance ** 0.5
            sharpe_ratio = mean_pnl / std_pnl if std_pnl > 0 else 0.0
        else:
            sharpe_ratio = None

        # Determine date range
        actual_start = min(t.meeting_date for t in trades)
        actual_end = max(t.meeting_date for t in trades)

        result = BacktestResult(
            start_date=actual_start,
            end_date=actual_end,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=round(total_pnl, 4),
            hit_rate=round(hit_rate, 4),
            average_edge=round(average_edge, 4),
            sharpe_ratio=round(sharpe_ratio, 4) if sharpe_ratio else None,
            trades=trades
        )

        # Audit the backtest
        self.audit.log_action(
            action_type="fed_rate_backtest",
            action_data={
                "start_date": result.start_date,
                "end_date": result.end_date,
                "total_trades": result.total_trades,
                "hit_rate": result.hit_rate,
                "total_pnl": result.total_pnl
            },
            result="completed"
        )

        return result

    def generate_report(self, result: BacktestResult) -> str:
        """
        Generate a human-readable backtest report.

        Args:
            result: BacktestResult from run_backtest

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("  FED RATE BACKTEST REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Period: {result.start_date} to {result.end_date}")
        report.append(f"Total FOMC Meetings: {result.total_trades}")
        report.append("")
        report.append("PERFORMANCE SUMMARY")
        report.append("-" * 40)
        report.append(f"Winning Trades: {result.winning_trades}")
        report.append(f"Losing Trades:  {result.losing_trades}")
        report.append(f"Hit Rate:       {result.hit_rate:.1%}")
        report.append("")
        report.append(f"Total P&L:      ${result.total_pnl:.2f} (per $1 bet)")
        report.append(f"Average Edge:   {result.average_edge:.1%}")
        if result.sharpe_ratio is not None:
            report.append(f"Sharpe Ratio:   {result.sharpe_ratio:.2f}")
        report.append("")

        if result.trades:
            report.append("TRADE DETAILS")
            report.append("-" * 40)
            for trade in result.trades[:10]:  # Show first 10
                status = "✓" if trade.was_correct else "✗"
                report.append(
                    f"{status} {trade.meeting_date}: "
                    f"Predicted {trade.predicted_outcome}, "
                    f"Actual {trade.actual_outcome}, "
                    f"P&L: ${trade.pnl:+.2f}"
                )
            if len(result.trades) > 10:
                report.append(f"... and {len(result.trades) - 10} more trades")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


def run_backtest_cli(output_path: Optional[Path] = None) -> int:
    """
    CLI entry point for running backtests.

    Args:
        output_path: Optional path to write results

    Returns:
        Exit code (0 for success)
    """
    print("🔬 Fed Rate Backtester")
    print("=" * 50)
    print()

    backtester = FedRateBacktester()

    # Use default model fair prices for backtesting
    # These represent what the model typically predicts
    model_fair_prices = {
        "25bps cut": 0.65,
        "50bps cut": 0.10,
        "hold": 0.25,
        "25bps hike": 0.50,
        "50bps hike": 0.10,
        "75bps hike": 0.05,
    }

    # Run backtest
    result = backtester.run_backtest(
        model_fair_prices=model_fair_prices,
        start_date="2022-01-01",
        end_date="2024-12-31"
    )

    # Generate and print report
    report = backtester.generate_report(result)
    print(report)

    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result_dict = asdict(result)
        # Convert trades to dicts
        if result.trades:
            result_dict['trades'] = [asdict(t) for t in result.trades]

        output_tmp = output_path.with_suffix('.tmp')
        with open(output_tmp, 'w') as f:
            json.dump(result_dict, f, indent=2)
        output_tmp.replace(output_path)

        print(f"\nResults written to: {output_path}")

    return 0


def main():
    """Main entry point"""
    repo_root = Path(__file__).parent.parent
    output_path = repo_root / 'state' / 'fed_rate_backtest.json'

    try:
        return run_backtest_cli(output_path=output_path)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
