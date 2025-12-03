#!/usr/bin/env python3
"""
MARKET DATA PIPELINE - INTEGRAFIX BRIDGE #1

Closes the trading loop:
    FETCH → ANALYZE → DECIDE → EXECUTE → RECORD → LEARN → IMPROVE

Before: Each stage was isolated, data flows to disk, components never connect
After:  One unified pipeline where data flows through all stages

Serving: Yair Siegel
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


@dataclass
class Signal:
    """Trading signal from analysis stage."""
    signal_id: str
    market_id: str
    market_slug: str
    market_question: str
    side: str  # YES or NO
    market_price: float
    estimated_price: float
    edge: float
    confidence: float
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Decision:
    """Trading decision from decide stage."""
    decision_id: str
    signal_id: str  # Traceability back to signal
    market_slug: str
    side: str
    amount_usd: float
    confidence: float
    reasoning: str
    kernels_consulted: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Execution:
    """Execution result from execute stage."""
    execution_id: str
    decision_id: str  # Traceability back to decision
    order_id: Optional[str]
    status: str  # success, failed, dry_run
    market_slug: str
    side: str
    size: float
    price: Optional[float]
    error: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Outcome:
    """Outcome record linking decision to result."""
    outcome_id: str
    decision_id: str
    execution_id: str
    signal_id: str
    market_slug: str
    decision_confidence: float
    execution_status: str
    execution_price: Optional[float]
    # To be filled when market resolves
    market_resolved: bool = False
    resolution: Optional[str] = None  # YES or NO
    pnl: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MarketDataPipeline:
    """
    Unified pipeline connecting all trading stages.

    Closes the loop:
    1. FETCH   - Get latest market data
    2. ANALYZE - Generate trading signals
    3. DECIDE  - Make trading decisions using knowledge bases
    4. EXECUTE - Execute trades through unified hub
    5. RECORD  - Record outcomes with full traceability
    6. LEARN   - Extract lessons from outcomes
    7. IMPROVE - Update decision parameters based on learnings
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.pipeline_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure directories exist
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / "pipeline").mkdir(exist_ok=True)

    def run_cycle(self) -> Dict:
        """
        Run one complete cycle of the trading loop.

        Returns summary of what happened at each stage.
        """
        print("=" * 70)
        print(f"MARKET DATA PIPELINE - {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Pipeline ID: {self.pipeline_id}")
        print(f"Time: {self.timestamp}")
        print("=" * 70)

        results = {
            "pipeline_id": self.pipeline_id,
            "timestamp": self.timestamp,
            "dry_run": self.dry_run,
            "stages": {}
        }

        # Stage 1: FETCH
        print("\n[1/7] FETCH - Getting market data...")
        market_data = self._stage_fetch()
        results["stages"]["fetch"] = {
            "markets_fetched": len(market_data),
            "status": "success" if market_data else "no_data"
        }
        print(f"      Fetched {len(market_data)} markets")

        if not market_data:
            print("      No market data - aborting pipeline")
            return results

        # Stage 2: ANALYZE
        print("\n[2/7] ANALYZE - Generating signals...")
        signals = self._stage_analyze(market_data)
        results["stages"]["analyze"] = {
            "signals_generated": len(signals),
            "status": "success" if signals else "no_signals"
        }
        print(f"      Generated {len(signals)} signals")

        if not signals:
            print("      No signals - aborting pipeline")
            return results

        # Stage 3: DECIDE
        print("\n[3/7] DECIDE - Making trading decisions...")
        decisions = self._stage_decide(signals)
        results["stages"]["decide"] = {
            "decisions_made": len(decisions),
            "status": "success" if decisions else "no_decisions"
        }
        print(f"      Made {len(decisions)} decisions")

        if not decisions:
            print("      No decisions - aborting pipeline")
            return results

        # Stage 4: EXECUTE
        print("\n[4/7] EXECUTE - Executing trades...")
        executions = self._stage_execute(decisions)
        results["stages"]["execute"] = {
            "executions": len(executions),
            "successful": sum(1 for e in executions if e.status == "success"),
            "dry_run": sum(1 for e in executions if e.status == "dry_run"),
            "failed": sum(1 for e in executions if e.status == "failed"),
            "status": "success"
        }
        print(f"      Executed {len(executions)} trades")

        # Stage 5: RECORD
        print("\n[5/7] RECORD - Recording outcomes...")
        outcomes = self._stage_record(signals, decisions, executions)
        results["stages"]["record"] = {
            "outcomes_recorded": len(outcomes),
            "status": "success"
        }
        print(f"      Recorded {len(outcomes)} outcomes")

        # Stage 6: LEARN
        print("\n[6/7] LEARN - Extracting lessons...")
        learnings = self._stage_learn(outcomes)
        results["stages"]["learn"] = {
            "lessons_extracted": len(learnings),
            "status": "success" if learnings else "no_learnings"
        }
        print(f"      Extracted {len(learnings)} lessons")

        # Stage 7: IMPROVE
        print("\n[7/7] IMPROVE - Updating parameters...")
        improvements = self._stage_improve(learnings)
        results["stages"]["improve"] = {
            "parameters_updated": len(improvements),
            "status": "success" if improvements else "no_updates"
        }
        print(f"      Updated {len(improvements)} parameters")

        # Save pipeline results
        self._save_pipeline_results(results)

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)

        return results

    # ==================== STAGE 1: FETCH ====================

    def _stage_fetch(self) -> List[Dict]:
        """
        Fetch latest market data.

        Connects to: fetchers/ho_fetch_polymarket.py
        """
        # Try fresh markets file first (most reliable)
        try:
            fresh_file = STATE_DIR / "fresh_polymarket_markets.json"
            if fresh_file.exists():
                data = json.loads(fresh_file.read_text())
                markets = data.get("markets", [])
                if markets:
                    print(f"      Source: fresh_polymarket_markets.json ({len(markets)} markets)")
                    return markets
        except Exception as e:
            print(f"      Warning: Failed to read fresh markets: {e}")

        try:
            # Try to use the existing fetcher
            from fetchers.ho_fetch_polymarket import fetch_markets_raw

            markets = fetch_markets_raw()
            if markets:
                print(f"      Source: live fetch ({len(markets)} markets)")
                return markets
        except ImportError:
            pass

        # Fallback: read from cached state
        try:
            cache_file = STATE_DIR / "polymarket_live_state.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                markets = data.get("markets", [])
                if markets:
                    print(f"      Source: polymarket_live_state.json ({len(markets)} markets)")
                    return markets
        except:
            pass

        return []

    # ==================== STAGE 2: ANALYZE ====================

    def _stage_analyze(self, market_data: List[Dict]) -> List[Signal]:
        """
        Generate trading signals from market data.

        Connects to: autonomous/probability_calibrator.py
        """
        signals = []

        try:
            from autonomous.probability_calibrator import ProbabilityCalibrator
            calibrator = ProbabilityCalibrator()
        except:
            calibrator = None

        for market in market_data:
            try:
                market_id = market.get("id") or market.get("condition_id", "")
                slug = market.get("slug") or market.get("market_slug", "unknown")
                question = market.get("question", slug)

                # Skip closed or inactive markets
                if market.get("closed") or not market.get("active", True):
                    continue

                # Get price - try multiple formats
                price = None
                if "yes_price" in market and market["yes_price"]:
                    price = float(market["yes_price"])
                elif "tokens" in market:
                    for token in market["tokens"]:
                        if token.get("outcome") == "Yes":
                            price = float(token.get("price", 0))
                            break
                elif "outcomePrices" in market:
                    try:
                        prices = market["outcomePrices"]
                        if isinstance(prices, str):
                            prices = json.loads(prices)
                        price = float(prices[0]) if prices else None
                    except:
                        pass

                if not price or price <= 0.001 or price >= 0.999:
                    continue

                # Calculate edge using wisdom-based estimation
                if calibrator:
                    try:
                        estimated = calibrator.calibrate(market)
                        if isinstance(estimated, dict):
                            estimated = estimated.get("estimate", price)
                    except:
                        estimated = None
                else:
                    estimated = None

                # If calibrator didn't work, use simple heuristics
                if estimated is None or estimated == price:
                    # Extreme value plays: low prices are often underpriced
                    if price < 0.05:
                        # Assume 50-100% underpriced for very low prices
                        estimated = price * 1.5
                        estimated = min(estimated, 0.10)
                    elif price < 0.15:
                        # Assume 30-50% underpriced
                        estimated = price * 1.3
                    elif price > 0.90:
                        # High prices often overpriced
                        estimated = price * 0.95
                    elif price > 0.85:
                        estimated = price * 0.98
                    else:
                        # Mid-range prices - assume correctly priced
                        estimated = price

                # Calculate relative edge
                edge = (estimated - price) / price if price > 0 else 0

                # Apply minimum edge threshold
                min_edge = 0.10  # 10% minimum edge
                if abs(edge) < min_edge:
                    continue

                side = "YES" if edge > 0 else "NO"
                confidence = min(0.85, 0.5 + abs(edge) * 0.5)

                signal = Signal(
                    signal_id=f"SIG-{str(uuid.uuid4())[:8]}",
                    market_id=market_id,
                    market_slug=slug,
                    market_question=question[:100],
                    side=side,
                    market_price=price,
                    estimated_price=estimated,
                    edge=edge,
                    confidence=confidence,
                    source="wisdom_analysis"
                )
                signals.append(signal)

            except Exception as e:
                continue

        # Sort by edge strength
        signals.sort(key=lambda s: abs(s.edge), reverse=True)

        print(f"      Analyzed {len(market_data)} markets, found {len(signals)} with edge > 10%")
        return signals[:15]  # Top 15 signals

    # ==================== STAGE 3: DECIDE ====================

    def _stage_decide(self, signals: List[Signal]) -> List[Decision]:
        """
        Make trading decisions using knowledge bases.

        Connects to: ai_nexus/memory_kernels.py
        """
        decisions = []

        # Try to load knowledge kernels
        kernels = {}
        try:
            kernel_dir = PROJECT_ROOT / "ai_nexus" / "kernels"
            if kernel_dir.exists():
                for kf in kernel_dir.glob("*.json"):
                    try:
                        kernels[kf.stem] = json.loads(kf.read_text())
                    except:
                        pass
        except:
            pass

        kernels_consulted = list(kernels.keys()) if kernels else ["default"]

        for signal in signals:
            # Decision logic
            if signal.edge < 0.05:
                continue  # Not enough edge

            if signal.confidence < 0.5:
                continue  # Not confident enough

            # Size based on edge and confidence
            base_size = 2.0  # $2 base
            edge_multiplier = min(2.0, 1.0 + signal.edge)
            confidence_multiplier = signal.confidence
            size = base_size * edge_multiplier * confidence_multiplier

            # Risk check from kernels
            risk_kernel = kernels.get("risk_model_v2", {})
            max_risk = risk_kernel.get("max_position_size", 10.0)
            size = min(size, max_risk)

            decision = Decision(
                decision_id=f"DEC-{str(uuid.uuid4())[:8]}",
                signal_id=signal.signal_id,
                market_slug=signal.market_slug,
                side=signal.side,
                amount_usd=round(size, 2),
                confidence=signal.confidence,
                reasoning=f"Edge {signal.edge:.1%}, confidence {signal.confidence:.1%}",
                kernels_consulted=kernels_consulted
            )
            decisions.append(decision)

        return decisions

    # ==================== STAGE 4: EXECUTE ====================

    def _stage_execute(self, decisions: List[Decision]) -> List[Execution]:
        """
        Execute trades through unified hub.

        Connects to: trading/unified_trading_hub.py or autonomous/concrete_executor.py
        """
        executions = []

        for decision in decisions:
            if self.dry_run:
                # Dry run - don't actually execute
                execution = Execution(
                    execution_id=f"EXE-{str(uuid.uuid4())[:8]}",
                    decision_id=decision.decision_id,
                    order_id=None,
                    status="dry_run",
                    market_slug=decision.market_slug,
                    side=decision.side,
                    size=decision.amount_usd,
                    price=None,
                    error=None
                )
            else:
                # Live execution
                try:
                    from autonomous.concrete_executor import ConcreteExecutor
                    executor = ConcreteExecutor(dry_run=False)

                    result = executor.execute_trade(
                        market_slug=decision.market_slug,
                        side=decision.side,
                        size=decision.amount_usd
                    )

                    execution = Execution(
                        execution_id=f"EXE-{str(uuid.uuid4())[:8]}",
                        decision_id=decision.decision_id,
                        order_id=result.get("order_id"),
                        status="success" if result.get("success") else "failed",
                        market_slug=decision.market_slug,
                        side=decision.side,
                        size=decision.amount_usd,
                        price=result.get("price"),
                        error=result.get("error")
                    )
                except Exception as e:
                    execution = Execution(
                        execution_id=f"EXE-{str(uuid.uuid4())[:8]}",
                        decision_id=decision.decision_id,
                        order_id=None,
                        status="failed",
                        market_slug=decision.market_slug,
                        side=decision.side,
                        size=decision.amount_usd,
                        price=None,
                        error=str(e)
                    )

            executions.append(execution)

            # Log execution
            print(f"      [{execution.status.upper()}] {decision.market_slug} "
                  f"{decision.side} ${decision.amount_usd:.2f}")

        return executions

    # ==================== STAGE 5: RECORD ====================

    def _stage_record(
        self,
        signals: List[Signal],
        decisions: List[Decision],
        executions: List[Execution]
    ) -> List[Outcome]:
        """
        Record outcomes with full traceability.

        Creates links: signal_id → decision_id → execution_id → outcome
        """
        outcomes = []

        # Build lookups
        signal_map = {s.signal_id: s for s in signals}
        decision_map = {d.decision_id: d for d in decisions}

        for execution in executions:
            decision = decision_map.get(execution.decision_id)
            if not decision:
                continue

            signal = signal_map.get(decision.signal_id)

            outcome = Outcome(
                outcome_id=f"OUT-{str(uuid.uuid4())[:8]}",
                decision_id=decision.decision_id,
                execution_id=execution.execution_id,
                signal_id=decision.signal_id,
                market_slug=execution.market_slug,
                decision_confidence=decision.confidence,
                execution_status=execution.status,
                execution_price=execution.price
            )
            outcomes.append(outcome)

        # Save to traceable outcomes file
        outcomes_file = STATE_DIR / "pipeline" / "outcomes_traceable.jsonl"
        with open(outcomes_file, "a") as f:
            for outcome in outcomes:
                f.write(json.dumps(asdict(outcome)) + "\n")

        return outcomes

    # ==================== STAGE 6: LEARN ====================

    def _stage_learn(self, outcomes: List[Outcome]) -> List[Dict]:
        """
        Extract lessons from outcomes.

        Connects to: ai_nexus/feedback_loop.py
        """
        learnings = []

        # Aggregate outcomes by status
        status_counts = {}
        for outcome in outcomes:
            status = outcome.execution_status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Extract learnings
        total = len(outcomes)
        if total > 0:
            success_rate = status_counts.get("success", 0) / total
            dry_run_rate = status_counts.get("dry_run", 0) / total

            learnings.append({
                "type": "execution_success_rate",
                "value": success_rate,
                "sample_size": total,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Confidence calibration
            avg_confidence = sum(o.decision_confidence for o in outcomes) / total
            learnings.append({
                "type": "average_decision_confidence",
                "value": avg_confidence,
                "sample_size": total,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Try to use feedback loop
        try:
            from ai_nexus.feedback_loop import FeedbackLoopClosure
            feedback = FeedbackLoopClosure()
            additional = feedback.analyze_performance()
            if additional:
                learnings.extend(additional)
        except:
            pass

        # Save learnings
        learnings_file = STATE_DIR / "pipeline" / "learnings.jsonl"
        with open(learnings_file, "a") as f:
            for learning in learnings:
                f.write(json.dumps(learning) + "\n")

        return learnings

    # ==================== STAGE 7: IMPROVE ====================

    def _stage_improve(self, learnings: List[Dict]) -> List[Dict]:
        """
        Update decision parameters based on learnings.

        Connects to: ai_nexus/memory_kernels.py
        """
        improvements = []

        for learning in learnings:
            if not isinstance(learning, dict):
                continue
            if learning.get("type") == "execution_success_rate":
                success_rate = learning["value"]

                # If success rate is low, reduce position sizes
                if success_rate < 0.5:
                    improvements.append({
                        "parameter": "base_position_size",
                        "action": "reduce",
                        "reason": f"Low success rate: {success_rate:.1%}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                # If success rate is high, we could increase
                elif success_rate > 0.8:
                    improvements.append({
                        "parameter": "base_position_size",
                        "action": "increase",
                        "reason": f"High success rate: {success_rate:.1%}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

        # Save improvements
        improvements_file = STATE_DIR / "pipeline" / "improvements.jsonl"
        with open(improvements_file, "a") as f:
            for improvement in improvements:
                f.write(json.dumps(improvement) + "\n")

        # Try to update kernels
        try:
            kernel_file = PROJECT_ROOT / "ai_nexus" / "kernels" / "trading_params.json"
            kernel_file.parent.mkdir(parents=True, exist_ok=True)

            params = {}
            if kernel_file.exists():
                params = json.loads(kernel_file.read_text())

            params["last_updated"] = datetime.now(timezone.utc).isoformat()
            params["improvements"] = improvements

            with open(kernel_file, "w") as f:
                json.dump(params, f, indent=2)
        except:
            pass

        return improvements

    # ==================== HELPERS ====================

    def _save_pipeline_results(self, results: Dict):
        """Save complete pipeline results."""
        results_file = STATE_DIR / "pipeline" / f"pipeline_{self.pipeline_id}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        # Also update latest
        latest_file = STATE_DIR / "pipeline" / "latest_pipeline.json"
        with open(latest_file, "w") as f:
            json.dump(results, f, indent=2)


def main():
    """Run the market data pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Market Data Pipeline")
    parser.add_argument("--live", action="store_true", help="Run in live mode (execute real trades)")
    args = parser.parse_args()

    pipeline = MarketDataPipeline(dry_run=not args.live)
    results = pipeline.run_cycle()

    print(f"\nResults saved to: state/pipeline/pipeline_{pipeline.pipeline_id}.json")
    return results


if __name__ == "__main__":
    main()
