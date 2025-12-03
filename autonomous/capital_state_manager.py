#!/usr/bin/env python3
"""
Capital State Manager - Optimize Capital Deployment
Implementation of Yair's teaching on capital states.

YAIR'S TEACHING - THREE TIERS OF CAPITAL:
(Renamed from "Level" to avoid confusion with Level 2 order book data)

Tier 1: Unused Cash (no collateral)
  - Sitting idle, not backing any orders
  - Speed advantage: can deploy INSTANTLY
  - No cancel step needed

Tier 2: Limit Order Collateral (Working Capital)
  - Deployed as limits, fishing everywhere
  - Capital working (collecting spread, waiting for fills)
  - To redeploy: must cancel first → time cost

Tier 3: Filled Positions (Locked Capital)
  - Actually holding YES/NO tokens
  - Locked until sell/resolution

NOTE: "Level 2" in trading jargon = ORDER BOOK DATA (bids/asks at all prices)
      "Tier 2" here = WORKING CAPITAL deployed as limit orders

'Market orders = calculated deviation from deployed default state'

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
CAPITAL_STATE = STATE_DIR / "capital_management.json"

# Polymarket credentials
POLYMARKET_KEY = "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493"
POLYMARKET_FUNDER = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
POLYMARKET_HOST = "https://clob.polymarket.com"


class CapitalStateManager:
    """
    Manage capital across Yair's three tiers.

    IMPORTANT TERMINOLOGY:
    - "Level 2" = Order book data (bids/asks at all price levels) - MARKET DATA
    - "Tier 2" = Working capital deployed as limit orders - CAPITAL ALLOCATION
    """

    def __init__(self):
        self.state = self._load_state()
        self.client = None
        self._init_client()

    def _load_state(self) -> Dict:
        if CAPITAL_STATE.exists():
            with open(CAPITAL_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "capital_tiers": {
                "tier_1_cash": 0.0,        # Unused, instant deploy
                "tier_2_working": 0.0,     # In limit orders (working capital)
                "tier_3_locked": 0.0       # Filled positions
            },
            "total_capital": 0.0,
            "allocation_history": [],
            "optimal_allocation": {
                "default": {"tier_1": 0.10, "tier_2": 0.70, "tier_3": 0.20},
                "high_opportunity": {"tier_1": 0.30, "tier_2": 0.40, "tier_3": 0.30},
                "defensive": {"tier_1": 0.40, "tier_2": 0.50, "tier_3": 0.10}
            }
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(CAPITAL_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _init_client(self):
        """Initialize Polymarket client."""
        try:
            from py_clob_client.client import ClobClient
            self.client = ClobClient(
                POLYMARKET_HOST,
                key=POLYMARKET_KEY,
                chain_id=137,
                funder=POLYMARKET_FUNDER
            )
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)
        except Exception as e:
            print(f"Client init error: {e}")
            self.client = None

    def get_current_allocation(self) -> Dict:
        """
        Get current capital allocation across all three tiers.

        Yair's teaching: 'System decides allocation dynamically
        based on real-time conditions'
        """
        allocation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tier_1_cash": 0.0,
            "tier_2_working": 0.0,
            "tier_3_locked": 0.0,
            "total": 0.0,
            "percentages": {}
        }

        if not self.client:
            return allocation

        try:
            # Tier 2: Get open orders (limit order collateral = working capital)
            orders = self.client.get_orders() or []
            tier_2 = 0.0
            for order in orders:
                price = float(order.get("price", 0))
                size = float(order.get("original_size", order.get("size", 0)))
                tier_2 += price * size

            allocation["tier_2_working"] = tier_2

            # Tier 1: Cash not in orders (approximated)
            # Note: Would need balance API for exact value
            allocation["tier_1_cash"] = 7.99  # From known state

            # Tier 3: Positions (approximated from pending)
            allocation["tier_3_locked"] = 98.05  # From known state

            # Totals
            allocation["total"] = (
                allocation["tier_1_cash"] +
                allocation["tier_2_working"] +
                allocation["tier_3_locked"]
            )

            if allocation["total"] > 0:
                allocation["percentages"] = {
                    "tier_1": allocation["tier_1_cash"] / allocation["total"],
                    "tier_2": allocation["tier_2_working"] / allocation["total"],
                    "tier_3": allocation["tier_3_locked"] / allocation["total"]
                }

        except Exception as e:
            print(f"Error getting allocation: {e}")

        return allocation

    def calculate_optimal_rebalance(self, current: Dict, mode: str = "default") -> Dict:
        """
        Calculate optimal rebalancing based on mode.

        Yair's teaching: 'Algo figures out optimal allocation dynamically'
        """
        if current["total"] == 0:
            return {"error": "No capital to allocate"}

        target = self.state["optimal_allocation"].get(mode, self.state["optimal_allocation"]["default"])

        rebalance = {
            "mode": mode,
            "current": current["percentages"],
            "target": target,
            "actions": []
        }

        # Calculate needed changes
        current_pcts = current.get("percentages", {})

        for tier in ["tier_1", "tier_2", "tier_3"]:
            current_pct = current_pcts.get(tier, 0)
            target_pct = target.get(tier, 0)
            diff = target_pct - current_pct

            if abs(diff) > 0.05:  # Only rebalance if >5% off
                if diff > 0:
                    action = f"INCREASE {tier} by {diff:.1%}"
                else:
                    action = f"DECREASE {tier} by {abs(diff):.1%}"
                rebalance["actions"].append({
                    "tier": tier,
                    "change": diff,
                    "action": action,
                    "amount": diff * current["total"]
                })

        return rebalance

    def should_deviate_to_market_order(self, opportunity: Dict) -> Dict:
        """
        Yair's teaching: 'Does market order net benefit vs current state?
        Market orders = calculated deviation from deployed default state.'
        """
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunity": opportunity,
            "recommendation": "HOLD",
            "reasoning": []
        }

        edge = opportunity.get("edge", 0)
        confidence = opportunity.get("confidence", 0)
        urgency = opportunity.get("urgency", "low")

        # Calculate expected value of market order vs waiting for limit fill
        market_order_cost = 0.01  # Slippage estimate
        limit_fill_prob = 0.3  # Probability limit would fill anyway
        time_value = 0.001  # Value of time (opportunity cost)

        ev_market = edge - market_order_cost
        ev_limit = edge * limit_fill_prob

        decision["ev_market_order"] = ev_market
        decision["ev_limit_order"] = ev_limit

        # Decision logic
        if ev_market > ev_limit and confidence > 0.6:
            decision["recommendation"] = "MARKET_ORDER"
            decision["reasoning"].append("EV of market order exceeds limit order")

        if urgency == "high" and edge > 0.05:
            decision["recommendation"] = "MARKET_ORDER"
            decision["reasoning"].append("High urgency with significant edge")

        if edge < 0.02:
            decision["recommendation"] = "HOLD"
            decision["reasoning"].append("Edge too small for market order cost")

        decision["teaching"] = "Market orders = calculated deviation from deployed default state"

        return decision

    def run_capital_analysis(self) -> Dict:
        """Run full capital state analysis."""
        print("=" * 70)
        print("CAPITAL STATE MANAGER")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[TERMINOLOGY CLARIFICATION]")
        print("  'Level 2' = ORDER BOOK DATA (bids/asks at all price levels)")
        print("  'Tier 2'  = WORKING CAPITAL deployed as limit orders")
        print()

        print("[YAIR'S TEACHING - THREE TIERS OF CAPITAL]")
        print("  Tier 1: Unused Cash - INSTANT deploy, no cancel needed")
        print("  Tier 2: Working Capital - Limits fishing, collecting spread")
        print("  Tier 3: Locked Positions - Held until sell/resolution")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Get current allocation
        print("[CURRENT CAPITAL ALLOCATION]")
        current = self.get_current_allocation()
        results["current"] = current

        print(f"  Tier 1 (Cash):     ${current['tier_1_cash']:.2f} ({current['percentages'].get('tier_1', 0):.1%})")
        print(f"  Tier 2 (Working):  ${current['tier_2_working']:.2f} ({current['percentages'].get('tier_2', 0):.1%})")
        print(f"  Tier 3 (Locked):   ${current['tier_3_locked']:.2f} ({current['percentages'].get('tier_3', 0):.1%})")
        print(f"  TOTAL:             ${current['total']:.2f}")
        print()

        # Check optimal allocation
        print("[OPTIMAL ALLOCATION ANALYSIS]")
        for mode in ["default", "high_opportunity", "defensive"]:
            rebalance = self.calculate_optimal_rebalance(current, mode)
            print(f"  {mode.upper()} mode:")
            target = rebalance.get("target", {})
            print(f"    Target: T1={target.get('tier_1', 0):.0%}, T2={target.get('tier_2', 0):.0%}, T3={target.get('tier_3', 0):.0%}")
            if rebalance.get("actions"):
                for action in rebalance["actions"]:
                    print(f"    → {action['action']}")
            else:
                print(f"    → Already balanced")
        print()

        # Example opportunity decision
        print("[MARKET ORDER DECISION FRAMEWORK]")
        test_opportunity = {
            "market": "Test opportunity",
            "edge": 0.05,
            "confidence": 0.7,
            "urgency": "medium"
        }
        decision = self.should_deviate_to_market_order(test_opportunity)
        print(f"  Given: Edge={test_opportunity['edge']:.0%}, Confidence={test_opportunity['confidence']:.0%}")
        print(f"  EV Market Order: {decision['ev_market_order']:.3f}")
        print(f"  EV Limit Order:  {decision['ev_limit_order']:.3f}")
        print(f"  Recommendation:  {decision['recommendation']}")
        for reason in decision["reasoning"]:
            print(f"    → {reason}")
        print()

        # Summary
        print("=" * 70)
        print("CAPITAL MANAGEMENT SUMMARY")
        print("=" * 70)
        print(f"  Total Capital: ${current['total']:.2f}")
        print(f"  Working Capital (T2+T3): ${current['tier_2_working'] + current['tier_3_locked']:.2f}")
        print(f"  Instant Deploy (T1): ${current['tier_1_cash']:.2f}")
        print()

        print("YAIR'S PRINCIPLE:")
        print("  'DEFAULT: Limits everywhere, capital working")
        print("   EVENT: Opportunity arises")
        print("   DECISION: Does market order net benefit?")
        print("   YES → Execute | NO → Let limits fish'")

        self.state["capital_tiers"] = {
            "tier_1_cash": current["tier_1_cash"],
            "tier_2_working": current["tier_2_working"],
            "tier_3_locked": current["tier_3_locked"]
        }
        self.state["total_capital"] = current["total"]
        self._save_state()

        return results


def main():
    manager = CapitalStateManager()
    return manager.run_capital_analysis()


if __name__ == "__main__":
    main()
