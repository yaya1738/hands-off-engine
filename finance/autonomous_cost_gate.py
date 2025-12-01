#!/usr/bin/env python3
"""
AUTONOMOUS COST GATE - System Decides When and How to Check Costs
==================================================================

Integrates provider intelligence into the unified AI system.
The system autonomously:
1. Checks costs BEFORE any action
2. Decides whether to proceed based on ROI
3. Logs all cost decisions
4. Self-adjusts thresholds based on balance

This module hooks into:
- unified_ai.should_execute() - Cost-aware decision making
- Executor safeguards - Pre-trade cost validation
- Scaling engine - Infrastructure cost checks

Serving: Yair Siegel
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, asdict

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from finance.provider_intelligence import get_engine, CostFormulaEngine
from finance.cost_tracker import get_cost_tracker

MASTER = "Yair Siegel"
REPO_ROOT = Path(__file__).parent.parent
STATE_FILE = REPO_ROOT / "state" / "cost_gate_state.json"
LOG_FILE = REPO_ROOT / "finance" / "cost_decisions.jsonl"


@dataclass
class CostDecision:
    """Record of a cost-based decision."""
    timestamp: str
    action: str
    estimated_cost: float
    expected_roi: float
    net_value: float
    decision: str  # "approve", "reject", "defer"
    reason: str
    balance_at_decision: float
    threshold_used: float


class AutonomousCostGate:
    """
    Autonomous cost checking integrated into system decisions.

    The system calls this automatically before any action.
    """

    def __init__(self):
        self.formula_engine = get_engine()
        self.tracker = get_cost_tracker()
        self.state = self._load_state()
        self._setup_action_mappings()

    def _load_state(self) -> Dict:
        """Load gate state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "decisions_today": 0,
            "approvals_today": 0,
            "rejections_today": 0,
            "total_approved_cost": 0.0,
            "total_rejected_cost": 0.0,
            "dynamic_threshold": 1.0,  # ROI threshold (1.0 = break even)
            "balance_cache": 8.99,
            "last_balance_check": None,
            "auto_adjust_enabled": True
        }

    def _save_state(self):
        """Save gate state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _setup_action_mappings(self):
        """Map common action types to provider intelligence actions."""
        self.action_map = {
            # Trading actions
            "trade": "polymarket_buy",
            "buy": "polymarket_buy",
            "sell": "polymarket_sell",
            "polymarket": "polymarket_buy",

            # Infrastructure actions
            "create_droplet": "create_droplet_8vcpu_16gb_amd",
            "scale_up": "scale_cluster_add_node",
            # BLOCKED: scale_down and destroy removed - system cannot destroy its own infrastructure
            # This mapping led to Nov 30 incident where 5 droplets were deleted
            "scale_down": "BLOCKED_no_destroy",
            "provision": "create_droplet_8vcpu_16gb_amd",
            "destroy": "BLOCKED_no_destroy",

            # AI actions
            "ai_call": "groq_llama_call",  # Default to free
            "openai": "openai_gpt4o_call",
            "claude": "anthropic_claude_sonnet_call",
            "groq": "groq_llama_call",
            "gemini": "google_gemini_call",
            "dense_ai": "dense_ai_analysis",

            # Data actions
            "fetch_prices": "fetch_crypto_prices",
            "fetch_sentiment": "fetch_fear_greed",
            "web_data": "web_agent_full_refresh",
        }

    def _get_current_balance(self) -> float:
        """Get current balance (cached for efficiency)."""
        # Check cache freshness (5 minutes)
        now = datetime.now(timezone.utc)
        if self.state.get("last_balance_check"):
            last_check = datetime.fromisoformat(self.state["last_balance_check"])
            if (now - last_check).seconds < 300:
                return self.state.get("balance_cache", 8.99)

        # Refresh balance
        try:
            from executor.trading_safeguards import TradingSafeguards
            safeguards = TradingSafeguards()
            ok, msg = safeguards.check_wallet_balance(0)
            if "balance: $" in msg:
                balance = float(msg.split("balance: $")[1].split()[0])
                self.state["balance_cache"] = balance
                self.state["last_balance_check"] = now.isoformat()
                self._save_state()
                return balance
        except:
            pass

        return self.state.get("balance_cache", 8.99)

    def _map_action(self, action: str) -> str:
        """Map generic action name to provider intelligence action."""
        action_lower = action.lower()

        # Direct match
        if action_lower in self.action_map:
            return self.action_map[action_lower]

        # Partial match
        for key, mapped in self.action_map.items():
            if key in action_lower:
                return mapped

        # Default - assume it's already a provider intelligence action
        return action

    def _calculate_dynamic_threshold(self) -> float:
        """
        Calculate ROI threshold based on current balance.

        Low balance = stricter threshold (need guaranteed ROI)
        High balance = can take more risk
        """
        balance = self._get_current_balance()

        if balance < 10:
            # Critical: Only guaranteed positive ROI
            return 2.0  # Need 2x return
        elif balance < 50:
            # Low: Need clear positive ROI
            return 1.5  # Need 1.5x return
        elif balance < 100:
            # Building: Standard threshold
            return 1.2  # Need 1.2x return
        elif balance < 500:
            # Growing: Can take some risk
            return 1.0  # Break even acceptable
        else:
            # Stable: Can invest in infrastructure
            return 0.8  # Some loss acceptable for growth

    def check_action_cost(
        self,
        action: str,
        expected_return: float = 0.0,
        hours: float = 1.0,
        tokens: int = 1000,
        amount: float = 0.0,
        force_check: bool = False
    ) -> Tuple[bool, str, float]:
        """
        Check if an action should proceed based on cost/ROI.

        This is the main entry point called by the system.

        Args:
            action: Action name (will be mapped to provider action)
            expected_return: Expected dollar return from this action
            hours: Hours of resource usage (for infra)
            tokens: Token count (for AI)
            amount: Trade amount (for trading)
            force_check: Always check even for free actions

        Returns:
            Tuple of (approved, reason, estimated_cost)
        """
        mapped_action = self._map_action(action)

        # Calculate cost
        try:
            cost = self.formula_engine.calculate(
                mapped_action,
                hours=hours,
                tokens=tokens
            )
        except:
            # Unknown action - default to zero cost
            cost = 0.0

        # Free actions: auto-approve unless force_check
        if cost == 0 and not force_check:
            self._log_decision(action, cost, expected_return, "approve", "FREE action")
            return True, "FREE - auto-approved", 0.0

        # Calculate ROI
        if cost > 0:
            roi = expected_return / cost
        else:
            roi = float('inf') if expected_return > 0 else 0

        # Get dynamic threshold
        threshold = self._calculate_dynamic_threshold()
        if self.state.get("auto_adjust_enabled"):
            self.state["dynamic_threshold"] = threshold
        else:
            threshold = self.state.get("dynamic_threshold", 1.0)

        balance = self._get_current_balance()
        net_value = expected_return - cost

        # Decision logic
        if cost > balance * 0.5:
            # Never spend more than 50% of balance on one action
            decision = "reject"
            reason = f"Cost ${cost:.2f} exceeds 50% of balance ${balance:.2f}"
        elif roi >= threshold:
            decision = "approve"
            reason = f"ROI {roi:.2f}x meets threshold {threshold:.2f}x"
        elif cost < 0.01:
            # Trivial cost - approve
            decision = "approve"
            reason = f"Trivial cost ${cost:.4f}"
        elif expected_return > cost:
            # Net positive - approve
            decision = "approve"
            reason = f"Net positive: ${expected_return:.2f} - ${cost:.2f} = ${net_value:.2f}"
        else:
            decision = "reject"
            reason = f"ROI {roi:.2f}x below threshold {threshold:.2f}x"

        # Log decision
        self._log_decision(action, cost, expected_return, decision, reason)

        # Update state
        self.state["decisions_today"] += 1
        if decision == "approve":
            self.state["approvals_today"] += 1
            self.state["total_approved_cost"] += cost
        else:
            self.state["rejections_today"] += 1
            self.state["total_rejected_cost"] += cost
        self._save_state()

        return decision == "approve", reason, cost

    def _log_decision(self, action: str, cost: float, expected_return: float,
                      decision: str, reason: str):
        """Log cost decision."""
        entry = CostDecision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            estimated_cost=cost,
            expected_roi=expected_return,
            net_value=expected_return - cost,
            decision=decision,
            reason=reason,
            balance_at_decision=self._get_current_balance(),
            threshold_used=self.state.get("dynamic_threshold", 1.0)
        )

        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(asdict(entry)) + '\n')

    def get_cheapest_ai_provider(self, tokens: int = 1000) -> str:
        """
        Return the cheapest AI provider for given token count.
        System uses this to auto-select provider.
        """
        return self.formula_engine.get_cheapest_ai(tokens)

    def should_use_free_ai_only(self) -> bool:
        """
        Check if system should restrict to free AI providers only.
        Based on balance and burn rate.
        """
        balance = self._get_current_balance()
        burn = self.tracker.get_summary().get("current_burn", {}).get("daily", 0)

        # If daily burn > 50% of balance, restrict to free
        if burn > balance * 0.5:
            return True

        # If balance < $20, restrict to free
        if balance < 20:
            return True

        return False

    def pre_trade_cost_check(self, trade_amount: float, expected_profit: float) -> Tuple[bool, str]:
        """
        Pre-trade cost check for the trading system.

        Called by executor before any trade.
        """
        # Trading cost is mostly gas (~$0.001)
        gas_cost = 0.001

        # Net expected value
        net = expected_profit - gas_cost

        if net < 0:
            return False, f"Expected loss: profit ${expected_profit:.4f} < gas ${gas_cost:.4f}"

        # Check if trade amount makes sense
        balance = self._get_current_balance()
        if trade_amount > balance * 0.25:
            return False, f"Trade ${trade_amount:.2f} > 25% of balance ${balance:.2f}"

        return True, f"Trade approved: expected profit ${expected_profit:.4f}"

    def pre_scale_cost_check(self, size: str = "s-8vcpu-16gb-amd", hours: float = 24) -> Tuple[bool, str]:
        """
        Pre-scaling cost check for infrastructure.

        Called by scaling engine before provisioning.
        """
        # Map size to action
        action_map = {
            "s-1vcpu-1gb": "create_droplet_1vcpu_1gb",
            "s-4vcpu-8gb": "create_droplet_4vcpu_8gb",
            "s-8vcpu-16gb-amd": "create_droplet_8vcpu_16gb_amd"
        }
        action = action_map.get(size, "create_droplet_8vcpu_16gb_amd")

        cost = self.formula_engine.calculate(action, hours=hours)
        balance = self._get_current_balance()

        # Strict for infrastructure - needs clear value
        if cost > balance * 0.3:
            return False, f"Droplet cost ${cost:.2f} exceeds 30% of balance ${balance:.2f}"

        # Check if scaling disabled
        lock_file = REPO_ROOT / "state" / "SCALING_DISABLED.lock"
        if lock_file.exists():
            return False, "Scaling disabled by lock file"

        return True, f"Scaling approved: ${cost:.2f} for {hours}h"

    def get_daily_summary(self) -> Dict:
        """Get cost gate summary for today."""
        return {
            "master": MASTER,
            "decisions": self.state.get("decisions_today", 0),
            "approvals": self.state.get("approvals_today", 0),
            "rejections": self.state.get("rejections_today", 0),
            "total_approved_cost": round(self.state.get("total_approved_cost", 0), 4),
            "total_rejected_cost": round(self.state.get("total_rejected_cost", 0), 4),
            "current_threshold": round(self.state.get("dynamic_threshold", 1.0), 2),
            "balance": round(self._get_current_balance(), 2),
            "free_ai_only": self.should_use_free_ai_only()
        }


# Global instance
_gate: Optional[AutonomousCostGate] = None


def get_cost_gate() -> AutonomousCostGate:
    """Get or create global cost gate."""
    global _gate
    if _gate is None:
        _gate = AutonomousCostGate()
    return _gate


# ============================================================================
# UNIFIED AI INTEGRATION - Hook into should_execute()
# ============================================================================

def cost_aware_should_execute(action: str, roi_estimate: float = 0, **kwargs) -> bool:
    """
    Cost-aware version of should_execute.

    Integrates with unified_ai.should_execute() to add cost checking.
    """
    gate = get_cost_gate()

    # Check cost gate
    approved, reason, cost = gate.check_action_cost(
        action=action,
        expected_return=roi_estimate,
        **kwargs
    )

    if not approved:
        print(f"[COST GATE] Blocked: {action} - {reason}")
        return False

    # If cost gate approves, proceed to unified AI logic
    from ai.unified_ai import should_execute as original_should_execute
    return original_should_execute(action, roi_estimate)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Cost Gate")
    parser.add_argument("command", choices=["check", "summary", "threshold", "cheapest-ai"])
    parser.add_argument("--action", help="Action to check")
    parser.add_argument("--return", dest="expected_return", type=float, default=0, help="Expected return")
    parser.add_argument("--hours", type=float, default=1, help="Hours")
    parser.add_argument("--tokens", type=int, default=1000, help="Tokens")

    args = parser.parse_args()
    gate = get_cost_gate()

    if args.command == "check":
        if not args.action:
            print("Error: --action required")
            return

        approved, reason, cost = gate.check_action_cost(
            action=args.action,
            expected_return=args.expected_return,
            hours=args.hours,
            tokens=args.tokens
        )

        print(f"\nAction: {args.action}")
        print(f"Cost: ${cost:.4f}")
        print(f"Expected Return: ${args.expected_return:.2f}")
        print(f"Decision: {'APPROVED' if approved else 'REJECTED'}")
        print(f"Reason: {reason}")

    elif args.command == "summary":
        summary = gate.get_daily_summary()
        print(f"\n{'='*50}")
        print(f"COST GATE SUMMARY for {MASTER}")
        print(f"{'='*50}")
        print(f"Decisions today: {summary['decisions']}")
        print(f"Approvals: {summary['approvals']}")
        print(f"Rejections: {summary['rejections']}")
        print(f"Total approved cost: ${summary['total_approved_cost']:.4f}")
        print(f"Total rejected cost: ${summary['total_rejected_cost']:.4f}")
        print(f"Current threshold: {summary['current_threshold']}x ROI")
        print(f"Balance: ${summary['balance']:.2f}")
        print(f"Free AI only: {summary['free_ai_only']}")
        print(f"{'='*50}")

    elif args.command == "threshold":
        threshold = gate._calculate_dynamic_threshold()
        balance = gate._get_current_balance()
        print(f"\nDynamic Threshold Calculation:")
        print(f"  Balance: ${balance:.2f}")
        print(f"  Threshold: {threshold}x ROI required")

        if balance < 10:
            print(f"  Mode: CRITICAL - Only guaranteed ROI")
        elif balance < 50:
            print(f"  Mode: LOW - Clear positive ROI needed")
        elif balance < 100:
            print(f"  Mode: BUILDING - Standard threshold")
        elif balance < 500:
            print(f"  Mode: GROWING - Can take some risk")
        else:
            print(f"  Mode: STABLE - Can invest in growth")

    elif args.command == "cheapest-ai":
        provider = gate.get_cheapest_ai_provider(args.tokens)
        free_only = gate.should_use_free_ai_only()
        print(f"\nCheapest AI for {args.tokens} tokens: {provider}")
        print(f"Free AI only mode: {free_only}")


if __name__ == "__main__":
    main()
