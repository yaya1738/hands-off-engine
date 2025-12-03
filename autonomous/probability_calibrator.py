#!/usr/bin/env python3
"""
Probability Calibrator - Master the Core Skill
Implementation of Yair's teaching: 'Probability Assessment -
True probability of event vs what market says = EDGE'

YAIR'S TEACHING:
- Not what market says - what WE believe
- Confidence in our probability (meta-level)
- How probabilities change (Bayesian updating)
- Multiple models → Hyper model

This is THE core skill. Everything else flows from accurate probability.

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics
import math

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

# INTEGRAFIX: Wire in external fair price estimation
try:
    from integrafix.fair_price_estimator import get_estimator as get_fair_price_estimator
    FAIR_PRICE_AVAILABLE = True
except ImportError:
    FAIR_PRICE_AVAILABLE = False

MASTER = "Yair Siegel"
CALIBRATION_STATE = STATE_DIR / "probability_calibration.json"
PREDICTIONS_LOG = STATE_DIR / "predictions.jsonl"


class ProbabilityCalibrator:
    """
    Master probability estimation - the foundation of all edge.

    Yair's teaching: 'Edge = our prob vs market prob'
    """

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if CALIBRATION_STATE.exists():
            with open(CALIBRATION_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "predictions": [],  # Our predictions to track
            "calibration_buckets": {
                "0-10": {"predictions": 0, "correct": 0},
                "10-20": {"predictions": 0, "correct": 0},
                "20-30": {"predictions": 0, "correct": 0},
                "30-40": {"predictions": 0, "correct": 0},
                "40-50": {"predictions": 0, "correct": 0},
                "50-60": {"predictions": 0, "correct": 0},
                "60-70": {"predictions": 0, "correct": 0},
                "70-80": {"predictions": 0, "correct": 0},
                "80-90": {"predictions": 0, "correct": 0},
                "90-100": {"predictions": 0, "correct": 0}
            },
            "brier_scores": [],
            "by_category": {},
            "model_weights": {
                "fundamental": 0.25,
                "flow": 0.20,
                "statistical": 0.20,
                "sentiment": 0.15,
                "market": 0.20
            }
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(CALIBRATION_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_prediction(self, prediction: Dict):
        prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(PREDICTIONS_LOG, 'a') as f:
            f.write(json.dumps(prediction) + "\n")

    def estimate_probability(self, market_data: Dict) -> Dict:
        """
        Yair's teaching: Multiple models → Hyper Model

        INTEGRAFIX: Now uses EXTERNAL fair price estimation instead of
        circular market_price-based calculations.

        Combine:
        1. INTEGRAFIX Model - External fair price (orderbook, history, volatility)
        2. Statistical Model - Historical patterns
        3. Fundamental Model - Category-based adjustment
        4. Flow Model - What smart money is doing
        5. Market Model - What current price implies (lowest weight)
        """
        question = market_data.get("question", "")
        prices = json.loads(market_data.get("outcomePrices", "[]"))
        volume = float(market_data.get("volume", 0))

        if len(prices) < 2:
            return {"error": "No prices"}

        market_yes = float(prices[0])
        market_no = float(prices[1])

        estimates = {}
        confidences = {}

        # INTEGRAFIX: Use EXTERNAL fair price estimation (breaks circular dependency)
        if FAIR_PRICE_AVAILABLE:
            try:
                estimator = get_fair_price_estimator()
                # Convert to format expected by fair price estimator
                market_for_fp = {
                    "slug": market_data.get("slug", ""),
                    "question": question,
                    "yes_price": market_yes,
                    "no_price": market_no,
                    "bestBid": market_data.get("bestBid", 0),
                    "bestAsk": market_data.get("bestAsk", 0),
                    "volume": volume,
                    "endDate": market_data.get("endDate"),
                }
                fp_estimate = estimator.estimate_fair_price(market_for_fp)

                # Only use if it's actionable (real signal, not noise)
                if fp_estimate.is_actionable:
                    estimates["integrafix"] = fp_estimate.fair_price
                    confidences["integrafix"] = fp_estimate.confidence
                elif fp_estimate.source != "no_signal":
                    estimates["integrafix"] = fp_estimate.fair_price
                    confidences["integrafix"] = fp_estimate.confidence * 0.5
            except Exception:
                pass

        # 1. Market Model (baseline) - NOW LOWEST WEIGHT
        estimates["market"] = market_yes
        confidences["market"] = 0.3 if volume > 100000 else 0.2  # Reduced from 0.7/0.5

        # 2. Statistical Model - extreme prices often wrong
        if market_yes < 0.05:
            # Very low prices tend to be lower than true prob
            estimates["statistical"] = market_yes * 1.5
            confidences["statistical"] = 0.5  # Increased
        elif market_yes > 0.95:
            # Very high prices tend to be lower than market thinks
            estimates["statistical"] = market_yes * 0.98
            confidences["statistical"] = 0.5
        else:
            estimates["statistical"] = market_yes
            confidences["statistical"] = 0.3

        # 3. Fundamental Model - category-based adjustment
        q_lower = question.lower()
        if any(kw in q_lower for kw in ['fed', 'rate', 'inflation']):
            # Macro events - markets often underestimate stability
            if market_yes < 0.3:
                estimates["fundamental"] = market_yes * 0.8  # Status quo bias
            else:
                estimates["fundamental"] = market_yes
            confidences["fundamental"] = 0.5
        elif any(kw in q_lower for kw in ['trump', 'biden', 'election']):
            # Politics - high uncertainty
            estimates["fundamental"] = market_yes
            confidences["fundamental"] = 0.4
        else:
            estimates["fundamental"] = market_yes
            confidences["fundamental"] = 0.3

        # 4. Flow Model - volume as signal
        if volume > 1000000:
            # High volume = more information in price
            estimates["flow"] = market_yes
            confidences["flow"] = 0.6
        elif volume > 100000:
            estimates["flow"] = market_yes
            confidences["flow"] = 0.4
        else:
            # Low volume = less trust in price
            estimates["flow"] = market_yes
            confidences["flow"] = 0.2

        # 5. Sentiment Model (simplified)
        estimates["sentiment"] = market_yes  # Would integrate social data
        confidences["sentiment"] = 0.2

        # HYPER MODEL - Weighted combination
        # INTEGRAFIX: Updated weights to prioritize external estimation
        weights = {
            "integrafix": 0.35,  # NEW: External estimation gets highest weight
            "fundamental": 0.20,
            "flow": 0.15,
            "statistical": 0.15,
            "sentiment": 0.10,
            "market": 0.05,  # Reduced: Market price is input, not output
        }

        total_weight = 0
        weighted_sum = 0
        confidence_sum = 0

        for model, estimate in estimates.items():
            w = weights.get(model, 0.1)
            c = confidences.get(model, 0.3)
            weighted_sum += estimate * w * c
            total_weight += w * c
            confidence_sum += c * w

        if total_weight > 0:
            hyper_estimate = weighted_sum / total_weight
            hyper_confidence = confidence_sum / sum(w for k, w in weights.items() if k in estimates)
        else:
            hyper_estimate = market_yes
            hyper_confidence = 0.3

        # Calculate edge
        edge = hyper_estimate - market_yes

        return {
            "market": market_data.get("question", "")[:60],
            "market_price": market_yes,
            "our_estimate": round(hyper_estimate, 4),
            "confidence": round(hyper_confidence, 3),
            "edge": round(edge, 4),
            "edge_pct": f"{edge * 100:.1f}%",
            "model_estimates": estimates,
            "model_confidences": confidences,
            "signal": "BUY_YES" if edge > 0.03 else "BUY_NO" if edge < -0.03 else "NO_EDGE",
            "integrafix_wired": "integrafix" in estimates,  # Track if external estimation used
            "teaching": "Edge = our prob vs market prob (INTEGRAFIX: external estimation)"
        }

    def record_prediction(self, market_id: str, our_prob: float,
                         market_prob: float, confidence: float,
                         category: str = "general") -> Dict:
        """
        Record a prediction for future calibration.

        Yair's teaching: 'Track what works and what doesn't'
        """
        prediction = {
            "id": f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "market_id": market_id,
            "our_probability": our_prob,
            "market_probability": market_prob,
            "confidence": confidence,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resolved": False,
            "outcome": None
        }

        self.state["predictions"].append(prediction)

        # Keep last 500 predictions
        if len(self.state["predictions"]) > 500:
            self.state["predictions"] = self.state["predictions"][-500:]

        self._log_prediction(prediction)
        self._save_state()

        return prediction

    def resolve_prediction(self, prediction_id: str, outcome: bool) -> Dict:
        """
        Resolve a prediction and update calibration.

        Yair's teaching: 'Learn from metrics and outcomes'
        """
        for pred in self.state["predictions"]:
            if pred.get("id") == prediction_id:
                pred["resolved"] = True
                pred["outcome"] = 1.0 if outcome else 0.0

                our_prob = pred["our_probability"]
                actual = pred["outcome"]

                # Brier score
                brier = (our_prob - actual) ** 2
                self.state["brier_scores"].append(brier)
                if len(self.state["brier_scores"]) > 100:
                    self.state["brier_scores"] = self.state["brier_scores"][-100:]

                # Update calibration bucket
                bucket = f"{int(our_prob * 10) * 10}-{int(our_prob * 10) * 10 + 10}"
                if bucket in self.state["calibration_buckets"]:
                    self.state["calibration_buckets"][bucket]["predictions"] += 1
                    if outcome:
                        self.state["calibration_buckets"][bucket]["correct"] += 1

                # Update category performance
                cat = pred.get("category", "general")
                if cat not in self.state["by_category"]:
                    self.state["by_category"][cat] = {"brier_sum": 0, "count": 0}
                self.state["by_category"][cat]["brier_sum"] += brier
                self.state["by_category"][cat]["count"] += 1

                self._save_state()

                return {
                    "prediction_id": prediction_id,
                    "our_prob": our_prob,
                    "outcome": outcome,
                    "brier_score": brier,
                    "was_correct": (our_prob > 0.5) == outcome
                }

        return {"error": "Prediction not found"}

    def get_calibration_report(self) -> Dict:
        """
        Yair's teaching: 'Confidence in our probability -
        How sure are we in our estimate?'

        This measures meta-level accuracy.
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_brier": 0.0,
            "calibration": {},
            "by_category": {},
            "model_adjustment_suggestions": []
        }

        # Overall Brier score
        if self.state["brier_scores"]:
            report["overall_brier"] = statistics.mean(self.state["brier_scores"])

        # Calibration by bucket
        for bucket, data in self.state["calibration_buckets"].items():
            if data["predictions"] > 0:
                actual_rate = data["correct"] / data["predictions"]
                expected_rate = (int(bucket.split("-")[0]) + 5) / 100

                report["calibration"][bucket] = {
                    "predictions": data["predictions"],
                    "expected": expected_rate,
                    "actual": actual_rate,
                    "calibration_error": abs(expected_rate - actual_rate)
                }

                # Suggest adjustments
                if data["predictions"] >= 10:
                    if actual_rate > expected_rate + 0.1:
                        report["model_adjustment_suggestions"].append(
                            f"UNDERCONFIDENT in {bucket}% range - increase estimates"
                        )
                    elif actual_rate < expected_rate - 0.1:
                        report["model_adjustment_suggestions"].append(
                            f"OVERCONFIDENT in {bucket}% range - decrease estimates"
                        )

        # Category performance
        for cat, data in self.state["by_category"].items():
            if data["count"] > 0:
                report["by_category"][cat] = {
                    "brier_score": data["brier_sum"] / data["count"],
                    "predictions": data["count"]
                }

        return report

    def run_calibration_cycle(self) -> Dict:
        """Run full probability calibration analysis."""
        print("=" * 70)
        print("PROBABILITY CALIBRATOR")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING]")
        print("  'Edge = our prob vs market prob'")
        print("  'Not what market says - what WE believe'")
        print("  'Multiple models → Hyper Model'")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "estimates": []
        }

        # Get markets and estimate probabilities
        print("[PROBABILITY ESTIMATES]")
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 20},
                timeout=15
            )

            if response.status_code == 200:
                markets = response.json()

                for market in markets[:10]:
                    estimate = self.estimate_probability(market)
                    if "error" not in estimate:
                        results["estimates"].append(estimate)

                        if abs(estimate["edge"]) > 0.02:
                            print(f"  {estimate['signal']}: {estimate['market'][:40]}...")
                            print(f"    Market: {estimate['market_price']:.2f} | Ours: {estimate['our_estimate']:.2f}")
                            print(f"    Edge: {estimate['edge_pct']} | Confidence: {estimate['confidence']:.0%}")
                            print()

        except Exception as e:
            print(f"  Error fetching markets: {e}")

        # Calibration report
        print("[CALIBRATION STATUS]")
        report = self.get_calibration_report()
        results["calibration"] = report

        print(f"  Overall Brier Score: {report['overall_brier']:.4f}")
        print(f"  (Target: < 0.15, lower is better)")
        print()

        # Calibration by bucket
        if report["calibration"]:
            print("[CALIBRATION BY CONFIDENCE]")
            for bucket, data in sorted(report["calibration"].items()):
                status = "✓" if data["calibration_error"] < 0.1 else "!"
                print(f"  {status} {bucket}%: Expected {data['expected']:.0%}, Actual {data['actual']:.0%}")
            print()

        # Adjustment suggestions
        if report["model_adjustment_suggestions"]:
            print("[MODEL ADJUSTMENTS NEEDED]")
            for suggestion in report["model_adjustment_suggestions"]:
                print(f"  → {suggestion}")
            print()

        # Category performance
        if report["by_category"]:
            print("[PERFORMANCE BY CATEGORY]")
            for cat, data in sorted(report["by_category"].items(),
                                   key=lambda x: x[1]["brier_score"]):
                print(f"  {cat}: Brier {data['brier_score']:.4f} ({data['predictions']} predictions)")
            print()

        # Summary
        print("=" * 70)
        print("CALIBRATION SUMMARY")
        print("=" * 70)
        print(f"  Predictions tracked: {len(self.state['predictions'])}")
        print(f"  Brier scores logged: {len(self.state['brier_scores'])}")
        print(f"  Categories tracked: {len(self.state['by_category'])}")
        print()

        # Actionable edges
        edges = [e for e in results["estimates"] if abs(e["edge"]) > 0.03]
        if edges:
            print("ACTIONABLE EDGES (from Hyper Model):")
            for edge in sorted(edges, key=lambda x: abs(x["edge"]), reverse=True)[:5]:
                print(f"  {edge['signal']}: {edge['market'][:40]}")
                print(f"    Edge: {edge['edge_pct']} at {edge['confidence']:.0%} confidence")

        self._save_state()
        return results


def main():
    calibrator = ProbabilityCalibrator()
    return calibrator.run_calibration_cycle()


if __name__ == "__main__":
    main()
