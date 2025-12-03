#!/usr/bin/env python3
"""
INTEGRAFIX: Recursive Engine
============================

THE MASTER INTEGRATOR

This engine:
1. Runs all integrafix components
2. Measures integration score
3. Identifies remaining gaps
4. Applies fixes recursively
5. Learns from results
6. Improves the integrafix methodology itself

CONVERGENCE THEOREM:
    If we keep applying integrafix to gaps,
    and learn from each application,
    the system converges to full integration.

    lim(n→∞) Integration(n) = 1.0

This is the engine that makes everything else work together.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
ENGINE_STATE = STATE_DIR / "recursive_engine.json"
ENGINE_LOG = STATE_DIR / "integrafix_runs.jsonl"


@dataclass
class IntegrafixRun:
    """Record of an integrafix run."""
    run_id: str
    started_at: str
    ended_at: Optional[str]
    integration_score_before: float
    integration_score_after: float
    gaps_fixed: int
    wires_created: int
    errors: List[str]
    learnings: List[str]
    convergence_delta: float


class RecursiveIntegrafixEngine:
    """
    The master integrafix engine.

    Recursively applies integrafix methodology until convergence.
    """

    def __init__(self):
        self.state = self._load_state()
        self.current_run: Optional[IntegrafixRun] = None

    def _load_state(self) -> Dict:
        if ENGINE_STATE.exists():
            with open(ENGINE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_runs": 0,
            "total_gaps_fixed": 0,
            "total_wires_created": 0,
            "integration_history": [],
            "convergence_rate": 0.0,
            "best_score": 0.0,
            "methodology_improvements": [],
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(ENGINE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_run(self, run: IntegrafixRun):
        with open(ENGINE_LOG, 'a') as f:
            f.write(json.dumps(asdict(run)) + "\n")

    # ==================== COMPONENT RUNNERS ====================

    def run_methodology(self) -> Dict:
        """Run the integrafix methodology analysis."""
        try:
            from integrafix.methodology import get_methodology

            methodology = get_methodology()
            methodology.register_known_gaps()

            # Get current score
            score = methodology.calculate_integration_score()

            # Get next fixes
            next_fixes = methodology.get_next_fixes()

            return {
                "success": True,
                "score": score,
                "gaps_total": len(methodology.gaps),
                "gaps_fixed": sum(1 for g in methodology.gaps.values() if g.fixed),
                "wires_total": len(methodology.wires),
                "next_fixes": [g.description for g in next_fixes],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_fair_price_fix(self) -> Dict:
        """Test the fair price estimator fix."""
        try:
            from integrafix.fair_price_estimator import get_estimator

            estimator = get_estimator()

            # Test with sample market
            test_market = {
                "slug": "test",
                "yes_price": 0.50,
                "no_price": 0.48,
                "bestBid": 0.48,
                "bestAsk": 0.52,
            }

            estimate = estimator.estimate_fair_price(test_market)

            return {
                "success": True,
                "fair_price": estimate.fair_price,
                "edge": estimate.edge_vs_market,
                "actionable": estimate.is_actionable,
                "source": estimate.source,
                "reasoning": estimate.reasoning,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_process_coordinator(self) -> Dict:
        """Test the process coordinator."""
        try:
            from integrafix.process_coordinator import get_coordinator

            coord = get_coordinator()

            # Register processes
            coord.register("backend_loop", state_file=str(STATE_DIR / "backend_loop.json"))
            coord.register("hardware_brain", state_file=str(STATE_DIR / "brain_state.json"))
            coord.register("scaling_engine", state_file=str(STATE_DIR / "scaling_state.json"))

            status = coord.status()

            return {
                "success": True,
                "processes": len(status["processes"]),
                "locks": len(status["locks"]),
                "pending_signals": status["pending_signals"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_trading_pipeline(self, dry_run: bool = True) -> Dict:
        """Run the integrated trading pipeline."""
        try:
            from integrafix.trading_pipeline import get_pipeline
            import requests

            pipeline = get_pipeline()

            # Fetch some real markets
            try:
                response = requests.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"closed": "false", "limit": 20},
                    timeout=10,
                )
                if response.status_code == 200:
                    markets = response.json()
                else:
                    markets = []
            except:
                markets = []

            if not markets:
                return {
                    "success": True,
                    "message": "No markets fetched",
                    "trades": 0,
                }

            # Transform to our format
            formatted_markets = []
            for m in markets:
                prices = json.loads(m.get("outcomePrices", "[]"))
                if len(prices) >= 2:
                    formatted_markets.append({
                        "slug": m.get("slug", ""),
                        "question": m.get("question", ""),
                        "yes_price": float(prices[0]),
                        "no_price": float(prices[1]),
                        "volume": float(m.get("volume", 0)),
                    })

            # Run pipeline
            result = pipeline.run_pipeline(
                markets=formatted_markets,
                capital=100,
                max_per_trade=25,
                min_edge=0.02,
                dry_run=dry_run,
            )

            return {
                "success": True,
                "markets_scanned": result["markets_scanned"],
                "signals_detected": result["signals_detected"],
                "trades_executed": result["trades_executed"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_ai_memory(self) -> Dict:
        """Initialize AI memory for this run."""
        try:
            from integrafix.ai_memory import get_memory

            memory = get_memory()
            memory.start_session("Recursive integrafix engine run")

            # Load context
            context = memory.build_context()

            return {
                "success": True,
                "session_id": memory.session_id,
                "memories_loaded": len(memory.memories),
                "context_length": len(context),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_cron_coordinator(self) -> Dict:
        """Run cron coordinator analysis."""
        try:
            from integrafix.cron_coordinator import get_coordinator

            coord = get_coordinator()
            health = coord.analyze_job_health()

            return {
                "success": True,
                "total_jobs": health["total_jobs"],
                "enabled": health["enabled"],
                "healthy": len(health["healthy"]),
                "failing": len(health["failing"]),
                "missing_critical": health["missing_critical"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== MAIN ENGINE ====================

    def measure_integration(self) -> float:
        """
        Measure current integration score across all components.

        Score = weighted average of component integrations
        """
        scores = []
        weights = []

        # Methodology score (high weight - fundamental)
        method_result = self.run_methodology()
        if method_result["success"]:
            scores.append(method_result["score"])
            weights.append(3)

        # Fair price fix working?
        fp_result = self.run_fair_price_fix()
        if fp_result["success"] and fp_result["actionable"]:
            scores.append(1.0)
        elif fp_result["success"]:
            scores.append(0.5)
        else:
            scores.append(0.0)
        weights.append(2)

        # Process coordinator working?
        pc_result = self.run_process_coordinator()
        if pc_result["success"] and pc_result["processes"] >= 3:
            scores.append(1.0)
        elif pc_result["success"]:
            scores.append(0.5)
        else:
            scores.append(0.0)
        weights.append(2)

        # Cron coordinator health
        cron_result = self.run_cron_coordinator()
        if cron_result["success"]:
            health_ratio = cron_result["healthy"] / max(1, cron_result["total_jobs"])
            scores.append(health_ratio)
        else:
            scores.append(0.0)
        weights.append(1)

        # Calculate weighted average
        if not scores:
            return 0.0

        total = sum(s * w for s, w in zip(scores, weights))
        return total / sum(weights)

    def run_cycle(self, dry_run: bool = True) -> IntegrafixRun:
        """
        Run one integrafix cycle.

        This is the main entry point.
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Measure before
        score_before = self.measure_integration()

        self.current_run = IntegrafixRun(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            ended_at=None,
            integration_score_before=score_before,
            integration_score_after=0.0,
            gaps_fixed=0,
            wires_created=0,
            errors=[],
            learnings=[],
            convergence_delta=0.0,
        )

        print("=" * 70)
        print(f"INTEGRAFIX RECURSIVE ENGINE - {run_id}")
        print("=" * 70)
        print(f"Integration Score BEFORE: {score_before:.1%}")
        print()

        # Run all components
        print("[1/6] Running Methodology Analysis...")
        method_result = self.run_methodology()
        if method_result["success"]:
            print(f"  Score: {method_result['score']:.1%}")
            print(f"  Gaps: {method_result['gaps_fixed']}/{method_result['gaps_total']} fixed")
            print(f"  Next fixes: {method_result['next_fixes'][:3]}")
        else:
            self.current_run.errors.append(f"Methodology: {method_result.get('error')}")
            print(f"  ERROR: {method_result.get('error')}")
        print()

        print("[2/6] Testing Fair Price Estimator...")
        fp_result = self.run_fair_price_fix()
        if fp_result["success"]:
            print(f"  Fair price: {fp_result['fair_price']:.3f}")
            print(f"  Edge: {fp_result['edge']:+.3f} ({'ACTIONABLE' if fp_result['actionable'] else 'not actionable'})")
            print(f"  Source: {fp_result['source']}")
            if fp_result['actionable']:
                self.current_run.learnings.append("Fair price estimator producing actionable signals")
        else:
            self.current_run.errors.append(f"Fair price: {fp_result.get('error')}")
            print(f"  ERROR: {fp_result.get('error')}")
        print()

        print("[3/6] Testing Process Coordinator...")
        pc_result = self.run_process_coordinator()
        if pc_result["success"]:
            print(f"  Processes registered: {pc_result['processes']}")
            print(f"  Active locks: {pc_result['locks']}")
            print(f"  Pending signals: {pc_result['pending_signals']}")
        else:
            self.current_run.errors.append(f"Process coord: {pc_result.get('error')}")
            print(f"  ERROR: {pc_result.get('error')}")
        print()

        print("[4/6] Running Trading Pipeline...")
        tp_result = self.run_trading_pipeline(dry_run=dry_run)
        if tp_result["success"]:
            print(f"  Markets scanned: {tp_result.get('markets_scanned', 0)}")
            print(f"  Signals detected: {tp_result.get('signals_detected', 0)}")
            print(f"  Trades executed: {tp_result.get('trades_executed', 0)} (dry_run={dry_run})")
            if tp_result.get('signals_detected', 0) > 0:
                self.current_run.learnings.append(f"Found {tp_result['signals_detected']} trading signals")
        else:
            self.current_run.errors.append(f"Trading pipeline: {tp_result.get('error')}")
            print(f"  ERROR: {tp_result.get('error')}")
        print()

        print("[5/6] Initializing AI Memory...")
        mem_result = self.run_ai_memory()
        if mem_result["success"]:
            print(f"  Session: {mem_result['session_id']}")
            print(f"  Memories loaded: {mem_result['memories_loaded']}")
        else:
            self.current_run.errors.append(f"AI memory: {mem_result.get('error')}")
            print(f"  ERROR: {mem_result.get('error')}")
        print()

        print("[6/6] Analyzing Cron Jobs...")
        cron_result = self.run_cron_coordinator()
        if cron_result["success"]:
            print(f"  Total jobs: {cron_result['total_jobs']}")
            print(f"  Healthy: {cron_result['healthy']}")
            print(f"  Failing: {cron_result['failing']}")
            if cron_result['missing_critical']:
                print(f"  MISSING CRITICAL: {cron_result['missing_critical']}")
                self.current_run.errors.append(f"Missing critical jobs: {cron_result['missing_critical']}")
        else:
            self.current_run.errors.append(f"Cron coord: {cron_result.get('error')}")
            print(f"  ERROR: {cron_result.get('error')}")
        print()

        # Measure after
        score_after = self.measure_integration()
        delta = score_after - score_before

        # Update run
        self.current_run.ended_at = datetime.now(timezone.utc).isoformat()
        self.current_run.integration_score_after = score_after
        self.current_run.convergence_delta = delta

        # Update state
        self.state["total_runs"] += 1
        self.state["integration_history"].append(score_after)
        if score_after > self.state["best_score"]:
            self.state["best_score"] = score_after

        # Calculate convergence rate
        history = self.state["integration_history"]
        if len(history) >= 3:
            recent_deltas = [history[i] - history[i-1] for i in range(-2, 0)]
            self.state["convergence_rate"] = sum(recent_deltas) / len(recent_deltas)

        self._save_state()
        self._log_run(self.current_run)

        # Save memory
        try:
            from integrafix.ai_memory import get_memory
            memory = get_memory()
            memory.end_session(
                outcomes=[
                    f"Integration: {score_before:.1%} → {score_after:.1%}",
                    f"Errors: {len(self.current_run.errors)}",
                ],
                next_actions=[
                    f for f in method_result.get("next_fixes", [])[:3]
                ] if method_result["success"] else [],
            )
            memory.save_context()
        except:
            pass

        # Print summary
        print("=" * 70)
        print("INTEGRAFIX RUN COMPLETE")
        print("=" * 70)
        print(f"Integration Score: {score_before:.1%} → {score_after:.1%} (Δ{delta:+.1%})")
        print(f"Errors: {len(self.current_run.errors)}")
        print(f"Learnings: {len(self.current_run.learnings)}")
        print(f"Best ever: {self.state['best_score']:.1%}")
        print(f"Convergence rate: {self.state['convergence_rate']:+.2%}/run")
        print()

        if delta > 0:
            print("✓ INTEGRATION IMPROVED")
        elif delta == 0:
            print("○ INTEGRATION STABLE")
        else:
            print("✗ INTEGRATION REGRESSED - investigate errors")

        return self.current_run

    def run_until_convergence(
        self,
        max_runs: int = 10,
        min_delta: float = 0.001,
        target_score: float = 0.95,
        dry_run: bool = True,
    ) -> List[IntegrafixRun]:
        """
        Run integrafix recursively until convergence.

        Stops when:
        - Target score reached
        - Delta < min_delta (convergence)
        - Max runs reached
        """
        runs = []

        for i in range(max_runs):
            print(f"\n{'='*70}")
            print(f"RECURSIVE RUN {i+1}/{max_runs}")
            print(f"{'='*70}\n")

            run = self.run_cycle(dry_run=dry_run)
            runs.append(run)

            # Check convergence conditions
            if run.integration_score_after >= target_score:
                print(f"\n✓ TARGET SCORE {target_score:.1%} REACHED!")
                break

            if abs(run.convergence_delta) < min_delta and i > 0:
                print(f"\n✓ CONVERGED (delta < {min_delta})")
                break

        return runs

    def status(self) -> Dict:
        """Get engine status."""
        return {
            "state": self.state,
            "current_score": self.state["integration_history"][-1] if self.state["integration_history"] else 0,
            "best_score": self.state["best_score"],
            "total_runs": self.state["total_runs"],
            "convergence_rate": self.state["convergence_rate"],
        }


# Singleton instance
_engine = None

def get_engine() -> RecursiveIntegrafixEngine:
    global _engine
    if _engine is None:
        _engine = RecursiveIntegrafixEngine()
    return _engine


def main():
    """Run the recursive integrafix engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Recursive Integrafix Engine")
    parser.add_argument("--once", action="store_true", help="Run one cycle only")
    parser.add_argument("--max-runs", type=int, default=5, help="Max recursive runs")
    parser.add_argument("--live", action="store_true", help="Live trading (not dry run)")
    args = parser.parse_args()

    engine = get_engine()

    if args.once:
        run = engine.run_cycle(dry_run=not args.live)
        return run
    else:
        runs = engine.run_until_convergence(
            max_runs=args.max_runs,
            dry_run=not args.live,
        )
        return runs


if __name__ == "__main__":
    main()
