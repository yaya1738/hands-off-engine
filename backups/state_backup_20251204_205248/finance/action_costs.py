#!/usr/bin/env python3
"""
ACTION COST MATRIX - Every Possible System Action and Its Cost
===============================================================

This module defines EVERY action the system can take and its cost breakdown.
Before ANY action, the system MUST consult this to know the cost.

PRINCIPLE: No action without cost awareness.

Action Categories:
1. INFRASTRUCTURE - DigitalOcean droplets, snapshots, bandwidth
2. AI_INFERENCE - API calls to AI providers
3. DATA_FETCH - External API calls for data
4. TRADING - Polymarket trades
5. STORAGE - Disk, snapshots, backups
6. NETWORK - Bandwidth, DNS
7. COMPUTE - CPU time, background jobs

Each action has:
- base_cost: Minimum cost per unit
- variable_cost: Cost that scales with usage
- time_component: How time affects cost (hourly, per-call, etc.)
- prerequisites: What must exist for this action
- side_effects: Other costs triggered by this action

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

BASE_DIR = Path(__file__).parent.parent
FINANCE_DIR = BASE_DIR / 'finance'

MASTER = "Yair Siegel"


class CostType(Enum):
    """How cost is calculated."""
    HOURLY = "hourly"           # Charged per hour (droplets)
    PER_CALL = "per_call"       # Charged per API call
    PER_TOKEN = "per_token"     # Charged per token (AI)
    PER_GB = "per_gb"           # Charged per GB (storage/bandwidth)
    PER_TRADE = "per_trade"     # Charged per trade
    FLAT = "flat"               # Flat fee
    FREE = "free"               # No cost (rate limited)


class Provider(Enum):
    """All providers."""
    DIGITALOCEAN = "digitalocean"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE_AI = "google_ai"
    POLYMARKET = "polymarket"
    COINGECKO = "coingecko"
    CRYPTOCOMPARE = "cryptocompare"
    ALTERNATIVE_ME = "alternative_me"
    GITHUB = "github"


@dataclass
class ActionCost:
    """Cost specification for an action."""
    action_id: str
    name: str
    provider: str
    cost_type: str
    base_cost: float
    unit: str
    variable_components: Dict[str, float] = field(default_factory=dict)
    time_multiplier: float = 1.0  # For hourly costs
    rate_limit: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    notes: str = ""

    def calculate(self, quantity: float = 1, duration_hours: float = 1) -> float:
        """Calculate total cost for this action."""
        if self.cost_type == CostType.HOURLY.value:
            return self.base_cost * duration_hours * quantity
        elif self.cost_type == CostType.FREE.value:
            return 0.0
        else:
            return self.base_cost * quantity


# =============================================================================
# COMPLETE ACTION COST MATRIX
# =============================================================================

ACTION_MATRIX: Dict[str, ActionCost] = {

    # =========================================================================
    # INFRASTRUCTURE - DigitalOcean
    # =========================================================================

    "do_create_droplet_small": ActionCost(
        action_id="do_create_droplet_small",
        name="Create Small Droplet (1 vCPU, 1GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.00744,
        unit="hour",
        variable_components={"monthly_cap": 5.0},
        notes="s-1vcpu-1gb - Cheapest option"
    ),

    "do_create_droplet_2gb": ActionCost(
        action_id="do_create_droplet_2gb",
        name="Create Droplet (1 vCPU, 2GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.01488,
        unit="hour",
        variable_components={"monthly_cap": 10.0},
        notes="s-1vcpu-2gb"
    ),

    "do_create_droplet_4gb": ActionCost(
        action_id="do_create_droplet_4gb",
        name="Create Droplet (2 vCPU, 4GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.02976,
        unit="hour",
        variable_components={"monthly_cap": 20.0},
        notes="s-2vcpu-4gb"
    ),

    "do_create_droplet_8gb": ActionCost(
        action_id="do_create_droplet_8gb",
        name="Create Droplet (4 vCPU, 8GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.05952,
        unit="hour",
        variable_components={"monthly_cap": 40.0},
        notes="s-4vcpu-8gb - Current pm-helper size"
    ),

    "do_create_droplet_16gb": ActionCost(
        action_id="do_create_droplet_16gb",
        name="Create Droplet (8 vCPU, 16GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.11905,
        unit="hour",
        variable_components={"monthly_cap": 80.0},
        notes="s-8vcpu-16gb"
    ),

    "do_create_droplet_16gb_amd": ActionCost(
        action_id="do_create_droplet_16gb_amd",
        name="Create AMD Droplet (8 vCPU, 16GB)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.14286,
        unit="hour",
        variable_components={"monthly_cap": 96.0},
        side_effects=["do_bandwidth_overage"],
        notes="s-8vcpu-16gb-amd - SCALING ENGINE DEFAULT"
    ),

    "do_destroy_droplet": ActionCost(
        action_id="do_destroy_droplet",
        name="Destroy Droplet",
        provider="digitalocean",
        cost_type=CostType.FLAT.value,
        base_cost=0.0,
        unit="action",
        notes="FREE - ONLY way to stop billing!"
    ),

    "do_snapshot": ActionCost(
        action_id="do_snapshot",
        name="Create Snapshot",
        provider="digitalocean",
        cost_type=CostType.PER_GB.value,
        base_cost=0.05,
        unit="GB/month",
        notes="Charged monthly per GB stored"
    ),

    "do_bandwidth_overage": ActionCost(
        action_id="do_bandwidth_overage",
        name="Bandwidth Overage",
        provider="digitalocean",
        cost_type=CostType.PER_GB.value,
        base_cost=0.01,
        unit="GB",
        notes="After free allowance exceeded"
    ),

    # =========================================================================
    # AI INFERENCE - OpenAI
    # =========================================================================

    "openai_gpt4_turbo": ActionCost(
        action_id="openai_gpt4_turbo",
        name="GPT-4 Turbo API Call",
        provider="openai",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.00001,  # $0.01 per 1K input
        unit="token",
        variable_components={
            "input_per_1k": 0.01,
            "output_per_1k": 0.03
        },
        prerequisites=["openai_credits_available"],
        notes="High quality, slow, expensive"
    ),

    "openai_gpt4o": ActionCost(
        action_id="openai_gpt4o",
        name="GPT-4o API Call",
        provider="openai",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.000005,
        unit="token",
        variable_components={
            "input_per_1k": 0.005,
            "output_per_1k": 0.015
        },
        prerequisites=["openai_credits_available"],
        notes="Balanced quality/cost"
    ),

    "openai_gpt35_turbo": ActionCost(
        action_id="openai_gpt35_turbo",
        name="GPT-3.5 Turbo API Call",
        provider="openai",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.0000005,
        unit="token",
        variable_components={
            "input_per_1k": 0.0005,
            "output_per_1k": 0.0015
        },
        prerequisites=["openai_credits_available"],
        notes="Cheapest OpenAI option"
    ),

    # =========================================================================
    # AI INFERENCE - Anthropic
    # =========================================================================

    "anthropic_claude_opus": ActionCost(
        action_id="anthropic_claude_opus",
        name="Claude Opus API Call",
        provider="anthropic",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.000015,
        unit="token",
        variable_components={
            "input_per_1k": 0.015,
            "output_per_1k": 0.075
        },
        notes="Highest quality, most expensive"
    ),

    "anthropic_claude_sonnet": ActionCost(
        action_id="anthropic_claude_sonnet",
        name="Claude Sonnet API Call",
        provider="anthropic",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.000003,
        unit="token",
        variable_components={
            "input_per_1k": 0.003,
            "output_per_1k": 0.015
        },
        notes="Balanced quality/cost"
    ),

    "anthropic_claude_haiku": ActionCost(
        action_id="anthropic_claude_haiku",
        name="Claude Haiku API Call",
        provider="anthropic",
        cost_type=CostType.PER_TOKEN.value,
        base_cost=0.00000025,
        unit="token",
        variable_components={
            "input_per_1k": 0.00025,
            "output_per_1k": 0.00125
        },
        notes="Cheapest Anthropic option"
    ),

    "anthropic_claude_code_pro": ActionCost(
        action_id="anthropic_claude_code_pro",
        name="Claude Code Pro Subscription",
        provider="anthropic",
        cost_type=CostType.FLAT.value,
        base_cost=100.0,
        unit="month",
        notes="Monthly subscription for Claude Code"
    ),

    # =========================================================================
    # AI INFERENCE - FREE TIERS
    # =========================================================================

    "groq_llama70b": ActionCost(
        action_id="groq_llama70b",
        name="Groq Llama 70B",
        provider="groq",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="request",
        rate_limit="30 RPM, 14400 RPD, 500K tokens/day",
        notes="FREE but rate limited - USE FIRST"
    ),

    "google_gemini_flash": ActionCost(
        action_id="google_gemini_flash",
        name="Google Gemini Flash",
        provider="google_ai",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="request",
        rate_limit="60 RPM, 1M tokens/day",
        notes="FREE but rate limited - USE SECOND"
    ),

    # =========================================================================
    # DATA PROVIDERS - All FREE
    # =========================================================================

    "coingecko_price": ActionCost(
        action_id="coingecko_price",
        name="CoinGecko Price Fetch",
        provider="coingecko",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="request",
        rate_limit="10-30 calls/minute",
        notes="FREE - Crypto prices"
    ),

    "cryptocompare_news": ActionCost(
        action_id="cryptocompare_news",
        name="CryptoCompare News Fetch",
        provider="cryptocompare",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="request",
        rate_limit="100K calls/month",
        notes="FREE - Crypto news"
    ),

    "alternative_me_fng": ActionCost(
        action_id="alternative_me_fng",
        name="Fear & Greed Index Fetch",
        provider="alternative_me",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="request",
        rate_limit="Unlimited",
        notes="FREE - Fear & Greed"
    ),

    # =========================================================================
    # TRADING - Polymarket
    # =========================================================================

    "polymarket_trade": ActionCost(
        action_id="polymarket_trade",
        name="Polymarket Trade",
        provider="polymarket",
        cost_type=CostType.PER_TRADE.value,
        base_cost=0.0,
        unit="trade",
        variable_components={
            "gas_fee_avg": 0.001,  # ~$0.001 Polygon gas
            "slippage_pct": 0.5
        },
        prerequisites=["usdc_balance_available"],
        side_effects=["polymarket_position_lock"],
        notes="0% trading fee, small gas, funds locked until resolution"
    ),

    "polymarket_position_lock": ActionCost(
        action_id="polymarket_position_lock",
        name="Position Capital Lock",
        provider="polymarket",
        cost_type=CostType.FLAT.value,
        base_cost=0.0,
        unit="position",
        notes="Capital locked until market resolves - OPPORTUNITY COST"
    ),

    # =========================================================================
    # STORAGE & NETWORK
    # =========================================================================

    "github_storage": ActionCost(
        action_id="github_storage",
        name="GitHub Storage",
        provider="github",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="GB",
        rate_limit="Unlimited for public repos",
        notes="FREE for current usage"
    ),

    "github_actions": ActionCost(
        action_id="github_actions",
        name="GitHub Actions Minutes",
        provider="github",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="minute",
        rate_limit="2000 minutes/month free",
        notes="FREE tier - 2000 min/month"
    ),

    # =========================================================================
    # COMPOUND ACTIONS (Multiple costs)
    # =========================================================================

    "scale_cluster_up": ActionCost(
        action_id="scale_cluster_up",
        name="Scale Cluster Up (Add Node)",
        provider="digitalocean",
        cost_type=CostType.HOURLY.value,
        base_cost=0.14286,  # Default to AMD 16GB
        unit="hour",
        side_effects=[
            "do_create_droplet_16gb_amd",
            "do_bandwidth_overage"
        ],
        notes="COMPOUND: Creates droplet + ongoing hourly cost"
    ),

    "dense_ai_analysis": ActionCost(
        action_id="dense_ai_analysis",
        name="Dense AI Full Analysis",
        provider="multiple",
        cost_type=CostType.PER_CALL.value,
        base_cost=0.0,  # Tries free first
        unit="analysis",
        side_effects=[
            "groq_llama70b",      # Try first (free)
            "google_gemini_flash", # Try second (free)
            "openai_gpt4_turbo"   # Fallback (paid)
        ],
        notes="COMPOUND: Uses free providers first, falls back to paid"
    ),

    "web_agent_refresh": ActionCost(
        action_id="web_agent_refresh",
        name="Web Agent Data Refresh",
        provider="multiple",
        cost_type=CostType.FREE.value,
        base_cost=0.0,
        unit="refresh",
        side_effects=[
            "coingecko_price",
            "alternative_me_fng",
            "cryptocompare_news"
        ],
        notes="COMPOUND: All free API calls"
    ),
}


# =============================================================================
# COST CALCULATOR
# =============================================================================

class ActionCostCalculator:
    """
    Calculate costs before taking actions.

    Usage:
        calc = ActionCostCalculator()
        cost = calc.estimate("do_create_droplet_16gb_amd", duration_hours=24)
        if cost > budget:
            reject_action()
    """

    def __init__(self):
        self.actions = ACTION_MATRIX

    def get_action(self, action_id: str) -> Optional[ActionCost]:
        """Get action cost spec."""
        return self.actions.get(action_id)

    def estimate(
        self,
        action_id: str,
        quantity: float = 1,
        duration_hours: float = 1,
        include_side_effects: bool = True
    ) -> Dict[str, Any]:
        """
        Estimate total cost for an action.

        Returns:
            {
                "action": action_id,
                "base_cost": float,
                "side_effect_costs": {...},
                "total_cost": float,
                "warnings": [...]
            }
        """
        action = self.get_action(action_id)
        if not action:
            return {"error": f"Unknown action: {action_id}"}

        base = action.calculate(quantity, duration_hours)
        side_effect_costs = {}
        warnings = []

        # Check prerequisites
        for prereq in action.prerequisites:
            warnings.append(f"REQUIRES: {prereq}")

        # Calculate side effects
        if include_side_effects:
            for effect_id in action.side_effects:
                effect = self.get_action(effect_id)
                if effect:
                    effect_cost = effect.calculate(quantity, duration_hours)
                    side_effect_costs[effect_id] = effect_cost

        total = base + sum(side_effect_costs.values())

        # Add rate limit warnings
        if action.rate_limit:
            warnings.append(f"RATE LIMIT: {action.rate_limit}")

        return {
            "action": action_id,
            "name": action.name,
            "provider": action.provider,
            "quantity": quantity,
            "duration_hours": duration_hours,
            "base_cost": round(base, 6),
            "side_effect_costs": {k: round(v, 6) for k, v in side_effect_costs.items()},
            "total_cost": round(total, 6),
            "cost_type": action.cost_type,
            "unit": action.unit,
            "warnings": warnings,
            "notes": action.notes
        }

    def estimate_compound(self, actions: List[Tuple[str, float, float]]) -> Dict:
        """
        Estimate cost for multiple actions.

        Args:
            actions: List of (action_id, quantity, duration_hours)

        Returns:
            Combined cost estimate
        """
        estimates = []
        total = 0.0

        for action_id, qty, hours in actions:
            est = self.estimate(action_id, qty, hours)
            if "error" not in est:
                estimates.append(est)
                total += est["total_cost"]

        return {
            "actions": estimates,
            "combined_total": round(total, 6)
        }

    def get_cheapest_ai(self) -> str:
        """Get cheapest available AI provider."""
        # Order: Free first, then by cost
        priority = [
            "groq_llama70b",      # Free
            "google_gemini_flash", # Free
            "anthropic_claude_haiku",  # Cheapest paid
            "openai_gpt35_turbo",      # Cheap paid
            "anthropic_claude_sonnet", # Mid
            "openai_gpt4o",            # Mid
            "openai_gpt4_turbo",       # Expensive
            "anthropic_claude_opus"    # Most expensive
        ]
        return priority[0]

    def get_hourly_burn(self, droplet_sizes: List[str]) -> float:
        """Calculate hourly burn for given droplets."""
        total = 0.0
        for size in droplet_sizes:
            action_id = f"do_create_droplet_{size.replace('-', '_')}"
            action = self.get_action(action_id)
            if action:
                total += action.base_cost
        return total

    def should_proceed(
        self,
        action_id: str,
        budget: float,
        quantity: float = 1,
        duration_hours: float = 1
    ) -> Tuple[bool, str]:
        """
        Decision helper: Should we proceed with this action?

        Returns:
            (should_proceed, reason)
        """
        est = self.estimate(action_id, quantity, duration_hours)

        if "error" in est:
            return False, est["error"]

        if est["total_cost"] > budget:
            return False, f"Cost ${est['total_cost']:.4f} exceeds budget ${budget:.4f}"

        if est["warnings"]:
            for warn in est["warnings"]:
                if "REQUIRES:" in warn:
                    return False, warn

        return True, f"Cost ${est['total_cost']:.4f} within budget"

    def list_free_actions(self) -> List[str]:
        """List all free actions."""
        return [
            action_id for action_id, action in self.actions.items()
            if action.cost_type == CostType.FREE.value
        ]

    def list_actions_by_provider(self, provider: str) -> List[str]:
        """List all actions for a provider."""
        return [
            action_id for action_id, action in self.actions.items()
            if action.provider == provider
        ]

    def print_matrix(self):
        """Print full action cost matrix."""
        print(f"\n{'='*70}")
        print(f"ACTION COST MATRIX - {len(self.actions)} actions")
        print(f"{'='*70}")

        by_provider = {}
        for action_id, action in self.actions.items():
            if action.provider not in by_provider:
                by_provider[action.provider] = []
            by_provider[action.provider].append((action_id, action))

        for provider, actions in sorted(by_provider.items()):
            print(f"\n{provider.upper()}")
            print("-" * 40)
            for action_id, action in actions:
                cost_str = f"${action.base_cost:.5f}/{action.unit}"
                if action.cost_type == CostType.FREE.value:
                    cost_str = "FREE"
                print(f"  {action_id}: {cost_str}")


# Global instance
_calculator: Optional[ActionCostCalculator] = None


def get_calculator() -> ActionCostCalculator:
    """Get global calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = ActionCostCalculator()
    return _calculator


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Action Cost Calculator")
    parser.add_argument("command", choices=["matrix", "estimate", "free", "provider", "burn"])
    parser.add_argument("--action", help="Action ID to estimate")
    parser.add_argument("--quantity", type=float, default=1, help="Quantity")
    parser.add_argument("--hours", type=float, default=1, help="Duration in hours")
    parser.add_argument("--provider", help="Provider name")

    args = parser.parse_args()
    calc = get_calculator()

    if args.command == "matrix":
        calc.print_matrix()

    elif args.command == "estimate":
        if args.action:
            est = calc.estimate(args.action, args.quantity, args.hours)
            print(json.dumps(est, indent=2))
        else:
            print("--action required")

    elif args.command == "free":
        free = calc.list_free_actions()
        print(f"\nFREE ACTIONS ({len(free)}):")
        for action in free:
            print(f"  - {action}")

    elif args.command == "provider":
        if args.provider:
            actions = calc.list_actions_by_provider(args.provider)
            print(f"\nActions for {args.provider}:")
            for action in actions:
                print(f"  - {action}")
        else:
            providers = set(a.provider for a in ACTION_MATRIX.values())
            print(f"\nProviders: {sorted(providers)}")

    elif args.command == "burn":
        # Current droplets
        sizes = ["8gb", "16gb_amd", "16gb_amd", "16gb_amd"]  # Current cluster
        burn = calc.get_hourly_burn(sizes)
        print(f"\nCurrent burn rate (4 droplets):")
        print(f"  Hourly: ${burn:.4f}")
        print(f"  Daily: ${burn * 24:.2f}")
        print(f"  Monthly: ${burn * 24 * 30:.2f}")


if __name__ == "__main__":
    main()
