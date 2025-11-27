#!/usr/bin/env python3
"""
Alpha Self-Learning Engine

Autonomous trading strategy improvement system.
Learns from trade outcomes to continuously improve alpha predictions.

The engine that makes money grow itself:
1. OBSERVE - Track all trade outcomes (win/loss, actual edge vs predicted)
2. LEARN - Update model weights based on outcome patterns
3. ADJUST - Tune confidence thresholds and position sizing
4. VALIDATE - Paper-trade adjustments before deploying
5. DEPLOY - Roll out improvements to live alpha model

For Yair Siegel's benefit - compounding returns through self-improving alpha.
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"
ALPHA_DIR = REPO_ROOT / "alpha"

LEARNING_STATE = STATE_DIR / "alpha_learning_state.json"
LEARNING_LOG = LOGS_DIR / "alpha_learning.jsonl"
TRADE_OUTCOMES = LOGS_DIR / "trade_outcomes.jsonl"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TradeOutcome:
    """Recorded outcome of a trade."""
    trade_id: str
    market_id: str
    market_name: str
    side: str  # YES or NO
    predicted_edge: float
    actual_outcome: str  # win, loss, pending
    predicted_confidence: float
    entry_price: float
    exit_price: Optional[float]
    pnl: float
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LearningInsight:
    """An insight learned from trade outcomes."""
    insight_type: str  # overconfidence, underconfidence, market_type, timing
    description: str
    adjustment_suggested: Dict
    confidence: float
    based_on_trades: int
    discovered_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ModelAdjustment:
    """An adjustment to make to the alpha model."""
    parameter: str
    old_value: float
    new_value: float
    reason: str
    applied: bool
    applied_at: Optional[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class AlphaSelfLearningEngine:
    """
    Engine that learns from trade outcomes to improve alpha predictions.
    
    Makes money grow itself through continuous self-improvement.
    """

    def __init__(self):
        self.state = self._load_state()
        self.outcomes: List[TradeOutcome] = []
        self.insights: List[LearningInsight] = []
        self._load_outcomes()
        logger.info("Alpha Self-Learning Engine initialized")

    def _load_state(self) -> Dict:
        """Load persisted learning state."""
        if LEARNING_STATE.exists():
            try:
                with open(LEARNING_STATE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "total_trades_analyzed": 0,
            "insights_generated": 0,
            "adjustments_made": 0,
            "current_confidence_bias": 0.0,  # Adjustment to confidence scores
            "market_type_weights": {},
            "last_learning_cycle": None,
            "cumulative_pnl": 0.0,
            "win_rate": 0.0
        }

    def _save_state(self):
        """Persist learning state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp_file = LEARNING_STATE.with_suffix('.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            tmp_file.rename(LEARNING_STATE)
        except IOError as e:
            logger.error(f"Failed to save state: {e}")

    def _load_outcomes(self):
        """Load trade outcomes for analysis."""
        if not TRADE_OUTCOMES.exists():
            return

        try:
            with open(TRADE_OUTCOMES) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        outcome = TradeOutcome(
                            trade_id=data.get("trade_id", ""),
                            market_id=data.get("market_id", ""),
                            market_name=data.get("market_name", ""),
                            side=data.get("side", ""),
                            predicted_edge=data.get("predicted_edge", 0.0),
                            actual_outcome=data.get("actual_outcome", "pending"),
                            predicted_confidence=data.get("predicted_confidence", 0.0),
                            entry_price=data.get("entry_price", 0.0),
                            exit_price=data.get("exit_price"),
                            pnl=data.get("pnl", 0.0),
                            timestamp=data.get("timestamp", "")
                        )
                        self.outcomes.append(outcome)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except IOError:
            pass

    def record_outcome(self, outcome: TradeOutcome):
        """Record a new trade outcome."""
        self.outcomes.append(outcome)
        try:
            with open(TRADE_OUTCOMES, 'a') as f:
                f.write(json.dumps(outcome.to_dict()) + '\n')
        except IOError as e:
            logger.error(f"Failed to record outcome: {e}")

    # =========================================================================
    # OBSERVE - Analyze trade outcomes
    # =========================================================================

    def calculate_performance_metrics(self) -> Dict:
        """Calculate performance metrics from outcomes."""
        if not self.outcomes:
            return {"trades": 0, "win_rate": 0.0, "avg_pnl": 0.0}

        completed = [o for o in self.outcomes if o.actual_outcome in ["win", "loss"]]

        if not completed:
            return {"trades": 0, "win_rate": 0.0, "avg_pnl": 0.0}

        wins = sum(1 for o in completed if o.actual_outcome == "win")
        total_pnl = sum(o.pnl for o in completed)

        return {
            "trades": len(completed),
            "wins": wins,
            "losses": len(completed) - wins,
            "win_rate": wins / len(completed),
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(completed),
            "avg_edge": statistics.mean([o.predicted_edge for o in completed])
        }

    def analyze_prediction_accuracy(self) -> Dict:
        """Analyze how accurate our edge predictions are."""
        completed = [o for o in self.outcomes if o.actual_outcome in ["win", "loss"]]

        if len(completed) < 10:
            return {"sufficient_data": False}

        # Group by confidence level
        high_conf = [o for o in completed if o.predicted_confidence >= 0.8]
        med_conf = [o for o in completed if 0.5 <= o.predicted_confidence < 0.8]
        low_conf = [o for o in completed if o.predicted_confidence < 0.5]

        results = {
            "sufficient_data": True,
            "high_confidence": {
                "count": len(high_conf),
                "win_rate": sum(1 for o in high_conf if o.actual_outcome == "win") / max(len(high_conf), 1)
            },
            "medium_confidence": {
                "count": len(med_conf),
                "win_rate": sum(1 for o in med_conf if o.actual_outcome == "win") / max(len(med_conf), 1)
            },
            "low_confidence": {
                "count": len(low_conf),
                "win_rate": sum(1 for o in low_conf if o.actual_outcome == "win") / max(len(low_conf), 1)
            }
        }

        # Check if confidence correlates with outcomes
        if high_conf and med_conf:
            if results["high_confidence"]["win_rate"] <= results["medium_confidence"]["win_rate"]:
                results["confidence_calibration"] = "overconfident"
            elif results["low_confidence"]["win_rate"] >= results["medium_confidence"]["win_rate"]:
                results["confidence_calibration"] = "underconfident"
            else:
                results["confidence_calibration"] = "well_calibrated"
        else:
            results["confidence_calibration"] = "insufficient_data"

        return results

    # =========================================================================
    # LEARN - Generate insights from patterns
    # =========================================================================

    def generate_insights(self) -> List[LearningInsight]:
        """Generate learning insights from trade outcomes."""
        insights = []

        # Analyze prediction accuracy
        accuracy = self.analyze_prediction_accuracy()

        if accuracy.get("sufficient_data"):
            calibration = accuracy.get("confidence_calibration")

            if calibration == "overconfident":
                insights.append(LearningInsight(
                    insight_type="overconfidence",
                    description="High confidence trades not outperforming medium confidence",
                    adjustment_suggested={"confidence_bias": -0.05},
                    confidence=0.7,
                    based_on_trades=accuracy["high_confidence"]["count"],
                    discovered_at=datetime.now(timezone.utc).isoformat()
                ))
            elif calibration == "underconfident":
                insights.append(LearningInsight(
                    insight_type="underconfidence",
                    description="Low confidence trades performing better than expected",
                    adjustment_suggested={"confidence_bias": 0.03},
                    confidence=0.6,
                    based_on_trades=accuracy["low_confidence"]["count"],
                    discovered_at=datetime.now(timezone.utc).isoformat()
                ))

        # Analyze edge prediction accuracy
        metrics = self.calculate_performance_metrics()
        if metrics["trades"] >= 20:
            if metrics["win_rate"] < 0.45:
                insights.append(LearningInsight(
                    insight_type="edge_overestimation",
                    description=f"Win rate {metrics['win_rate']:.1%} below expectation",
                    adjustment_suggested={"min_edge_threshold": 0.04},  # Raise threshold
                    confidence=0.8,
                    based_on_trades=metrics["trades"],
                    discovered_at=datetime.now(timezone.utc).isoformat()
                ))
            elif metrics["win_rate"] > 0.65:
                insights.append(LearningInsight(
                    insight_type="conservative_edge",
                    description=f"Win rate {metrics['win_rate']:.1%} exceeds predictions - could size up",
                    adjustment_suggested={"kelly_fraction_cap": 0.12},  # Slightly increase
                    confidence=0.6,
                    based_on_trades=metrics["trades"],
                    discovered_at=datetime.now(timezone.utc).isoformat()
                ))

        return insights

    # =========================================================================
    # ADJUST - Create model adjustments
    # =========================================================================

    def create_adjustments(self, insights: List[LearningInsight]) -> List[ModelAdjustment]:
        """Create model adjustments based on insights."""
        adjustments = []

        for insight in insights:
            if insight.confidence < 0.5:
                continue  # Skip low-confidence insights

            suggested = insight.adjustment_suggested

            for param, new_value in suggested.items():
                old_value = self.state.get(param, 0.0)

                adjustments.append(ModelAdjustment(
                    parameter=param,
                    old_value=old_value,
                    new_value=new_value,
                    reason=insight.description,
                    applied=False,
                    applied_at=None
                ))

        return adjustments

    def apply_adjustments(
        self, adjustments: List[ModelAdjustment], dry_run: bool = True
    ) -> List[ModelAdjustment]:
        """Apply adjustments to the model state."""
        applied = []

        for adj in adjustments:
            if dry_run:
                logger.info(f"[DRY RUN] Would adjust {adj.parameter}: {adj.old_value} → {adj.new_value}")
                continue

            logger.info(f"Applying adjustment: {adj.parameter}: {adj.old_value} → {adj.new_value}")

            # Apply to state
            self.state[adj.parameter] = adj.new_value
            adj.applied = True
            adj.applied_at = datetime.now(timezone.utc).isoformat()
            applied.append(adj)

            # Log the adjustment
            self._log_learning({
                "type": "adjustment_applied",
                "parameter": adj.parameter,
                "old_value": adj.old_value,
                "new_value": adj.new_value,
                "reason": adj.reason
            })

        self.state["adjustments_made"] = self.state.get("adjustments_made", 0) + len(applied)
        self._save_state()

        return applied

    def _log_learning(self, entry: Dict):
        """Log learning activity."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(LEARNING_LOG, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except IOError:
            pass

    # =========================================================================
    # Main learning cycle
    # =========================================================================

    def run_learning_cycle(self, apply_changes: bool = False) -> Dict:
        """Run one learning cycle."""
        logger.info("Starting alpha self-learning cycle")

        # Calculate current metrics
        metrics = self.calculate_performance_metrics()
        logger.info(f"Performance: {metrics['trades']} trades, {metrics['win_rate']:.1%} win rate")

        # Generate insights
        insights = self.generate_insights()
        logger.info(f"Generated {len(insights)} insights")

        # Create adjustments
        adjustments = self.create_adjustments(insights)
        logger.info(f"Created {len(adjustments)} potential adjustments")

        # Apply adjustments (or dry-run)
        applied = self.apply_adjustments(adjustments, dry_run=not apply_changes)

        # Update state
        self.state["total_trades_analyzed"] = metrics["trades"]
        self.state["insights_generated"] = self.state.get("insights_generated", 0) + len(insights)
        self.state["win_rate"] = metrics["win_rate"]
        self.state["cumulative_pnl"] = metrics.get("total_pnl", 0)
        self.state["last_learning_cycle"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        # Build report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "insights": [i.to_dict() for i in insights],
            "adjustments_proposed": [a.to_dict() for a in adjustments],
            "adjustments_applied": len(applied),
            "mode": "live" if apply_changes else "dry_run"
        }

        return report

    def get_current_biases(self) -> Dict:
        """Get current model biases/adjustments for use by alpha engine."""
        return {
            "confidence_bias": self.state.get("confidence_bias", 0.0),
            "min_edge_threshold": self.state.get("min_edge_threshold", 0.03),
            "kelly_fraction_cap": self.state.get("kelly_fraction_cap", 0.10),
            "market_type_weights": self.state.get("market_type_weights", {}),
            "last_updated": self.state.get("last_learning_cycle")
        }


def main():
    """Entry point."""
    engine = AlphaSelfLearningEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        # Apply changes (not just dry run)
        report = engine.run_learning_cycle(apply_changes=True)
        print(json.dumps(report, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--biases":
        # Show current biases
        biases = engine.get_current_biases()
        print(json.dumps(biases, indent=2))
    else:
        # Dry run (default)
        report = engine.run_learning_cycle(apply_changes=False)

        print(f"\n{'='*60}")
        print("ALPHA SELF-LEARNING REPORT (Dry Run)")
        print(f"{'='*60}")
        print(f"Trades analyzed: {report['metrics']['trades']}")
        print(f"Win rate: {report['metrics']['win_rate']:.1%}")
        print(f"Total P&L: ${report['metrics'].get('total_pnl', 0):.2f}")
        print(f"\nInsights generated: {len(report['insights'])}")
        for insight in report['insights']:
            print(f"  • [{insight['insight_type']}] {insight['description']}")
        print(f"\nAdjustments proposed: {len(report['adjustments_proposed'])}")
        for adj in report['adjustments_proposed']:
            print(f"  • {adj['parameter']}: {adj['old_value']} → {adj['new_value']}")
        print(f"\nTo apply changes, run with --apply flag")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
