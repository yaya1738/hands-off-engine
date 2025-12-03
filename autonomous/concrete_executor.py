#!/usr/bin/env python3
"""
Concrete Executor - Makes Teaching REAL
Connects all teaching systems to actual trade execution.

THE PROBLEM: Teaching systems existed but were isolated from action.

THE SOLUTION: Every trade goes through this pipeline:
1. Wisdom Engine → Categorizes market, finds edge
2. Probability Calibrator → 5-model hyper estimate
3. Capital Manager → L1/L2/L3 allocation decision
4. Glitch Detector → Safety validation
5. EXECUTE → Actual trade placement
6. Record Outcome → Feed back to skill tracker

Serving: Yair Siegel
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
MASTER = "Yair Siegel"

# Import teaching systems
from autonomous.yair_wisdom_engine import YairWisdomEngine
from autonomous.probability_calibrator import ProbabilityCalibrator
from autonomous.capital_state_manager import CapitalStateManager
from autonomous.glitch_detector import GlitchDetector
from autonomous.skill_growth_tracker import SkillGrowthTracker
from autonomous.outcome_recorder import OutcomeRecorder

EXECUTION_LOG = STATE_DIR / "concrete_executions.jsonl"
PIPELINE_STATE = STATE_DIR / "pipeline_state.json"


class ConcreteExecutor:
    """
    Makes every teaching CONCRETE through action.

    Yair's teaching: 'Edge is discovered through doing, not theorized'
    """

    def __init__(self, dry_run: bool = True):
        # Initialize all teaching systems
        self.wisdom = YairWisdomEngine()
        self.probability = ProbabilityCalibrator()
        self.capital = CapitalStateManager()
        self.glitch = GlitchDetector()
        self.skills = SkillGrowthTracker()
        self.outcomes = OutcomeRecorder()  # INTEGRAFIX: Close the feedback loop

        self.dry_run = dry_run  # Safety: start in dry run mode

        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if PIPELINE_STATE.exists():
            with open(PIPELINE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "trades_evaluated": 0,
            "trades_executed": 0,
            "trades_blocked": 0,
            "total_edge_captured": 0,
            "pipeline_runs": 0
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(PIPELINE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_execution(self, execution: Dict):
        execution["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(EXECUTION_LOG, 'a') as f:
            f.write(json.dumps(execution) + "\n")

    def evaluate_opportunity(self, market_data: Dict) -> Dict:
        """
        Full pipeline evaluation of a trading opportunity.

        CONCRETE PIPELINE:
        1. Wisdom → What category? What edge applies?
        2. Probability → What's our hyper estimate vs market?
        3. Capital → What size? L1/L2/L3?
        4. Glitch → Is data safe?
        5. Decision → Execute or wait?
        """

        evaluation = {
            "market": market_data.get("question", "")[:80],
            "market_id": market_data.get("id", market_data.get("condition_id", "")),
            "pipeline_stages": {},
            "recommendation": None,
            "concrete_action": None
        }

        prices = json.loads(market_data.get("outcomePrices", "[]"))
        market_price = float(prices[0]) if prices else 0.5

        # STAGE 1: Wisdom - Categorize and find applicable teachings
        question = market_data.get("question", "")
        category_info = self.wisdom.categorize_market(question)
        category = category_info.get("category", "general")
        teachings = category_info.get("strategy", {})
        evaluation["pipeline_stages"]["wisdom"] = {
            "category": category,
            "teachings": teachings,
            "status": "APPLIED"
        }

        # STAGE 2: Probability - INTEGRAFIX: Use BOTH probability calibrator AND wisdom engine
        prob_result = self.probability.estimate_probability(market_data)
        prob_estimate = prob_result.get("our_estimate", market_price)
        prob_confidence = prob_result.get("confidence", 0.5)

        # INTEGRAFIX: Also get wisdom engine's smart edge (has real logic for extreme prices)
        wisdom_result = self.wisdom.calculate_smart_edge(market_data)
        wisdom_confidence = wisdom_result.get("confidence", 0)
        wisdom_analysis = wisdom_result.get("analysis", {})

        # Default to probability calibrator estimate
        our_estimate = prob_estimate
        confidence = prob_confidence
        edge_source = "probability"

        # For extreme prices (< 5% or > 95%), apply wisdom engine's insight
        # Yair's teaching: "Very low prices tend to be lower than true prob"
        # INTEGRAFIX: For extreme low prices, calculate edge as % of potential return
        if market_price < 0.05:
            # Extreme value play - massive upside if it hits
            # Edge = how much we think it's underpriced relative to payout
            # If price is 1% but we think 2%, that's 100% edge on the trade!
            estimated_true = market_price * 2.0  # More aggressive: assume 100% underpriced
            our_estimate = min(estimated_true, 0.15)  # Cap at 15%
            # Calculate edge as relative improvement, not absolute
            # This gives meaningful edge values for small prices
            edge = (our_estimate - market_price) / market_price if market_price > 0 else 0
            edge = min(edge, 0.5)  # Cap at 50% relative edge
            confidence = 0.60  # Higher confidence on extreme value plays
            edge_source = "wisdom_extreme_low"
        elif market_price > 0.95:
            # High prices often overconfident - small edge to fade
            estimated_true = market_price * 0.97
            our_estimate = max(estimated_true, 0.90)
            edge = abs(our_estimate - market_price)
            confidence = 0.50
            edge_source = "wisdom_extreme_high"
        elif wisdom_confidence > 0.5 and wisdom_analysis.get("value_zone") in ["extreme_low", "extreme_high"]:
            # Wisdom engine has high confidence on value zone
            edge_source = "wisdom"
            confidence = wisdom_confidence
            edge = abs(our_estimate - market_price)
        else:
            # Mid-range: use absolute edge
            edge = abs(our_estimate - market_price)

        evaluation["pipeline_stages"]["probability"] = {
            "market_price": market_price,
            "our_estimate": our_estimate,
            "confidence": confidence,
            "edge": edge,
            "direction": "YES" if our_estimate > market_price else "NO",
            "edge_source": edge_source,
            "prob_estimate": prob_estimate,
            "wisdom_confidence": wisdom_confidence,
            "status": "CALCULATED"
        }

        # STAGE 3: Capital - Determine allocation
        edge = abs(our_estimate - market_price)
        opportunity = {
            "edge": edge,
            "confidence": confidence,
            "market_price": market_price,
            "our_estimate": our_estimate
        }
        capital_decision = self.capital.should_deviate_to_market_order(opportunity)
        evaluation["pipeline_stages"]["capital"] = {
            "recommendation": capital_decision.get("recommendation", "LIMIT"),
            "reasoning": capital_decision.get("reasoning", []),
            "status": "DECIDED"
        }

        # STAGE 4: Glitch - Validate safety
        market_id = evaluation["market_id"]
        safety = self.glitch.validate_trade(market_data, market_id)
        evaluation["pipeline_stages"]["glitch"] = {
            "safe_to_trade": safety.get("safe_to_trade", False),
            "severity": safety.get("overall_severity", 0),
            "warnings": safety.get("all_warnings", []),
            "status": "VALIDATED" if safety.get("safe_to_trade") else "BLOCKED"
        }

        # STAGE 5: Decision
        self.state["trades_evaluated"] += 1

        if not safety.get("safe_to_trade"):
            evaluation["recommendation"] = "BLOCK"
            evaluation["concrete_action"] = {
                "action": "NO_TRADE",
                "reason": "Glitch detector flagged unsafe",
                "warnings": safety.get("all_warnings", [])
            }
            self.state["trades_blocked"] += 1
        elif edge < 0.02:  # Yair's teaching: need meaningful edge
            evaluation["recommendation"] = "SKIP"
            evaluation["concrete_action"] = {
                "action": "NO_TRADE",
                "reason": f"Edge too small ({edge:.1%})",
                "threshold": "2%"
            }
        elif confidence < 0.3:
            evaluation["recommendation"] = "SKIP"
            evaluation["concrete_action"] = {
                "action": "NO_TRADE",
                "reason": f"Confidence too low ({confidence:.1%})"
            }
        else:
            # We have edge, confidence, and safety - BUILD THE TRADE
            direction = "YES" if our_estimate > market_price else "NO"
            order_type = capital_decision.get("recommendation", "LIMIT")

            # Size based on Kelly-inspired formula (simplified)
            # Yair's teaching: 'Volume overwhelms mistakes' but also 'risk management'
            kelly_fraction = (edge * confidence) / (1 - edge) if edge < 1 else 0.01
            max_fraction = 0.05  # Never more than 5% of capital
            position_fraction = min(kelly_fraction, max_fraction)

            evaluation["recommendation"] = "TRADE"
            evaluation["concrete_action"] = {
                "action": "PLACE_ORDER",
                "direction": direction,
                "target_price": our_estimate,
                "limit_price": market_price + (0.01 if direction == "NO" else -0.01),
                "order_type": order_type,
                "edge": edge,
                "confidence": confidence,
                "position_fraction": position_fraction,
                "teachings_applied": [
                    f"Category: {category}",
                    f"Models used: {len(prob_result.get('model_estimates', {}))}",
                    f"Capital level: {order_type}"
                ]
            }
            self.state["total_edge_captured"] += edge
            self.state["trades_executed"] += 1

        return evaluation

    def execute_trade(self, evaluation: Dict) -> Dict:
        """
        Actually place the trade on Polymarket.

        Returns execution result for outcome recording.
        """
        if evaluation.get("recommendation") != "TRADE":
            return {"executed": False, "reason": evaluation.get("recommendation")}

        action = evaluation.get("concrete_action", {})

        # Import trading client
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs

            host = "https://clob.polymarket.com"
            key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

            if not key:
                return {"executed": False, "reason": "No API key configured"}

            client = ClobClient(host, key=key, chain_id=137, funder=funder)
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Build order
            # This is where teaching becomes ACTION
            market_id = evaluation.get("market_id")
            direction = action.get("direction", "YES")
            limit_price = action.get("limit_price", 0.5)

            # For now, use small test size
            size = 5  # $5 test trades

            order_args = OrderArgs(
                token_id=market_id,
                price=limit_price,
                size=size,
                side="BUY" if direction == "YES" else "SELL"
            )

            signed_order = client.create_order(order_args)
            result = client.post_order(signed_order)

            execution_result = {
                "executed": True,
                "order_id": result.get("orderID"),
                "market": evaluation.get("market"),
                "direction": direction,
                "price": limit_price,
                "size": size,
                "edge_at_entry": action.get("edge"),
                "teachings_applied": action.get("teachings_applied", [])
            }

            # Log for outcome tracking
            self._log_execution(execution_result)

            return execution_result

        except Exception as e:
            return {"executed": False, "error": str(e)}

    def record_outcome(self, trade_id: str, outcome: Dict) -> Dict:
        """
        Record trade outcome back to skill tracker.

        THE FEEDBACK LOOP:
        Trade → Outcome → Skill Measurement → Learning → Better Trades

        Yair's teaching: 'The 100 trade test'
        """
        outcome_record = {
            "trade_id": trade_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": outcome.get("result"),  # "win", "loss", "pending"
            "pnl": outcome.get("pnl", 0),
            "edge_captured": outcome.get("edge_captured", 0),
            "category": outcome.get("category"),
            "our_estimate": outcome.get("our_estimate"),
            "market_estimate": outcome.get("market_estimate"),
            "actual_outcome": outcome.get("actual_outcome")  # 1 or 0
        }

        # Feed to skill tracker for learning
        if outcome.get("result") in ["win", "loss"]:
            category = outcome.get("category", "general")

            # Update calibration
            if outcome.get("our_estimate") and outcome.get("actual_outcome") is not None:
                self.probability.record_outcome(
                    outcome["our_estimate"],
                    outcome["actual_outcome"]
                )

            # Update skill tracking
            self.skills.record_trade_outcome(
                category=category,
                won=outcome.get("result") == "win",
                edge=outcome.get("edge_captured", 0)
            )

        return outcome_record

    def run_pipeline(self, limit: int = 10) -> Dict:
        """
        Run the full concrete pipeline on live markets.
        """
        import requests

        print("=" * 70)
        print("CONCRETE EXECUTOR - Teaching → Action Pipeline")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[PIPELINE STAGES]")
        print("  1. Wisdom Engine → Categorize, find applicable teachings")
        print("  2. Probability Calibrator → 5-model hyper estimate")
        print("  3. Capital Manager → L1/L2/L3 allocation")
        print("  4. Glitch Detector → Safety validation")
        print("  5. Execute → Actual trade placement")
        print("  6. Record → Feed outcome to skill tracker")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markets_evaluated": 0,
            "trades_recommended": 0,
            "trades_skipped": 0,
            "trades_blocked": 0,
            "opportunities": []
        }

        # Fetch live markets
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": limit},
                timeout=15
            )

            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch markets: {response.status_code}")
                return results

            markets = response.json()
            results["markets_evaluated"] = len(markets)

            print(f"[EVALUATING {len(markets)} MARKETS]")
            print()

            for market in markets:
                evaluation = self.evaluate_opportunity(market)

                market_name = evaluation["market"][:50]
                recommendation = evaluation["recommendation"]

                if recommendation == "TRADE":
                    results["trades_recommended"] += 1
                    action = evaluation["concrete_action"]

                    print(f"  ✓ TRADE: {market_name}...")
                    print(f"    Direction: {action['direction']}")
                    print(f"    Edge: {action['edge']:.1%}")
                    print(f"    Confidence: {action['confidence']:.1%}")
                    print(f"    Order type: {action['order_type']}")
                    print(f"    Teachings: {', '.join(action['teachings_applied'][:2])}")

                    # INTEGRAFIX: Actually execute the trade!
                    if self.dry_run:
                        print(f"    [DRY RUN - Trade not executed]")
                        execution_result = {"executed": False, "reason": "dry_run"}
                    else:
                        print(f"    [EXECUTING TRADE...]")
                        execution_result = self.execute_trade(evaluation)

                        if execution_result.get("executed"):
                            print(f"    [EXECUTED] Order ID: {execution_result.get('order_id')}")

                            # INTEGRAFIX: Register trade with OutcomeRecorder for feedback loop
                            trade_data = {
                                "market_id": evaluation.get("market_id"),
                                "market": market_name,
                                "direction": action.get("direction"),
                                "entry_price": action.get("limit_price"),
                                "our_estimate": action.get("target_price"),
                                "market_estimate": evaluation["pipeline_stages"]["probability"]["market_price"],
                                "category": evaluation["pipeline_stages"]["wisdom"]["category"],
                                "size": 5,  # Default test size
                                "edge": action.get("edge")
                            }
                            trade_id = self.outcomes.register_trade(trade_data)
                            print(f"    [TRACKED] Trade ID: {trade_id}")
                            results["trades_executed"] = results.get("trades_executed", 0) + 1
                        else:
                            print(f"    [FAILED] {execution_result.get('reason', execution_result.get('error', 'Unknown'))}")

                    print()

                    results["opportunities"].append({
                        "market": market_name,
                        "action": action,
                        "execution": execution_result
                    })

                elif recommendation == "BLOCK":
                    results["trades_blocked"] += 1
                    print(f"  ✗ BLOCKED: {market_name}...")
                    print(f"    Reason: {evaluation['concrete_action'].get('reason', 'Safety')}")
                    print()

                else:
                    results["trades_skipped"] += 1

            print(f"[SKIPPED: {results['trades_skipped']} (edge too small or low confidence)]")
            print()

        except Exception as e:
            print(f"[ERROR] Pipeline failed: {e}")

        # Summary
        print("=" * 70)
        print("CONCRETE EXECUTION SUMMARY")
        print("=" * 70)
        print(f"  Markets evaluated: {results['markets_evaluated']}")
        print(f"  Trades recommended: {results['trades_recommended']}")
        print(f"  Trades executed: {results.get('trades_executed', 0)}")
        print(f"  Trades blocked (safety): {results['trades_blocked']}")
        print(f"  Trades skipped (no edge): {results['trades_skipped']}")
        print(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()

        print("[LIFETIME STATS]")
        print(f"  Total evaluated: {self.state['trades_evaluated']}")
        print(f"  Total executed: {self.state['trades_executed']}")
        print(f"  Total blocked: {self.state['trades_blocked']}")
        print(f"  Total edge captured: {self.state['total_edge_captured']:.1%}")
        print()

        # INTEGRAFIX: Check outcome recorder status
        pending_count = len([t for t in self.outcomes.pending.get("trades", {}).values()
                            if t.get("status") == "pending"])
        print("[FEEDBACK LOOP STATUS]")
        print(f"  Pending trades awaiting outcome: {pending_count}")
        print(f"  Total outcomes recorded: {self.outcomes.learning.get('total_outcomes', 0)}")
        print()

        self.state["pipeline_runs"] += 1
        self._save_state()

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Concrete Executor - INTEGRAFIX Pipeline")
    parser.add_argument("--live", action="store_true", help="Enable live trading (default: dry run)")
    parser.add_argument("--limit", type=int, default=10, help="Number of markets to evaluate")
    parser.add_argument("--check-outcomes", action="store_true", help="Check for resolved outcomes")
    args = parser.parse_args()

    executor = ConcreteExecutor(dry_run=not args.live)

    if args.check_outcomes:
        # Check for resolved markets and update learning
        print("=" * 70)
        print("CHECKING OUTCOME RESOLUTIONS")
        print("=" * 70)
        resolved = executor.outcomes.check_resolutions()
        if resolved:
            for outcome in resolved:
                status = "WIN" if outcome["won"] else "LOSS"
                print(f"  {status}: {outcome['market_name'][:50]}")
                print(f"    P&L: ${outcome['pnl']:.2f}")
        else:
            print("  No resolved markets found")
        print()

    return executor.run_pipeline(limit=args.limit)


if __name__ == "__main__":
    main()
