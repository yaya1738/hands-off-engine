#!/usr/bin/env python3
"""
AI API Cost Optimizer

Purpose: Ensure $250/month AI spend generates positive ROI
Given: 0.8 month runway, every dollar counts

Strategy:
1. Track all AI API costs
2. Attribute costs to value-generating activities
3. Cut non-ROI-generating usage
4. Maximize free tiers (Claude CLI subscription, free API credits)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Pricing per 1M tokens (input/output)
AI_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},  # OpenRouter
}

# Monthly budget allocation
MONTHLY_BUDGET_USD = 250.0
BUDGET_ALLOCATION = {
    "claude_max_subscription": 20.0,  # Fixed - Claude Pro/Max
    "chatgpt_plus": 20.0,             # Fixed - ChatGPT Plus
    "copilot_pro": 10.0,              # Fixed - GitHub Copilot
    "anthropic_api_variable": 100.0,  # Variable - for trading signals
    "openrouter_fallback": 50.0,      # Variable - fallback
    "other_apis": 50.0,               # Variable - misc
}


class AICostOptimizer:
    """Optimize AI costs for positive ROI"""

    def __init__(self, ledger_dir: Optional[str] = None):
        self.ledger_dir = Path(ledger_dir) if ledger_dir else Path(__file__).parent.parent / "logs" / "ai_costs"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.cost_file = self.ledger_dir / "ai_usage.jsonl"

    def log_usage(self, provider: str, model: str, input_tokens: int, output_tokens: int,
                  purpose: str, value_generated: float = 0.0):
        """Log an AI API usage event"""
        pricing = AI_PRICING.get(model, {"input": 5.0, "output": 15.0})
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "purpose": purpose,
            "value_generated": value_generated,
            "roi": (value_generated / cost * 100) if cost > 0 else 0
        }

        with open(self.cost_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        return entry

    def get_period_costs(self, days: int = 30) -> Dict:
        """Get costs for a period"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        costs = {
            "total_cost": 0.0,
            "total_value": 0.0,
            "by_purpose": {},
            "by_provider": {},
            "by_model": {},
            "entries": 0
        }

        if not self.cost_file.exists():
            return costs

        with open(self.cost_file) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                    if ts.replace(tzinfo=None) < cutoff:
                        continue

                    cost = entry.get("cost_usd", 0)
                    value = entry.get("value_generated", 0)
                    purpose = entry.get("purpose", "unknown")
                    provider = entry.get("provider", "unknown")
                    model = entry.get("model", "unknown")

                    costs["total_cost"] += cost
                    costs["total_value"] += value
                    costs["entries"] += 1

                    # By purpose
                    if purpose not in costs["by_purpose"]:
                        costs["by_purpose"][purpose] = {"cost": 0, "value": 0, "count": 0}
                    costs["by_purpose"][purpose]["cost"] += cost
                    costs["by_purpose"][purpose]["value"] += value
                    costs["by_purpose"][purpose]["count"] += 1

                    # By provider
                    if provider not in costs["by_provider"]:
                        costs["by_provider"][provider] = {"cost": 0, "count": 0}
                    costs["by_provider"][provider]["cost"] += cost
                    costs["by_provider"][provider]["count"] += 1

                    # By model
                    if model not in costs["by_model"]:
                        costs["by_model"][model] = {"cost": 0, "count": 0}
                    costs["by_model"][model]["cost"] += cost
                    costs["by_model"][model]["count"] += 1

                except (json.JSONDecodeError, KeyError):
                    continue

        costs["roi_pct"] = (costs["total_value"] / costs["total_cost"] * 100) if costs["total_cost"] > 0 else 0.0
        return costs

    def optimize_recommendations(self) -> List[Dict]:
        """Generate optimization recommendations"""
        costs = self.get_period_costs(30)
        recommendations = []

        # Check overall ROI
        if costs["total_cost"] > 0 and costs["roi_pct"] < 100:
            recommendations.append({
                "priority": "critical",
                "issue": f"Negative ROI: {costs['roi_pct']:.1f}%",
                "action": "AI spend must generate value > cost. Focus API usage on trading signals only.",
                "savings_potential": costs["total_cost"] * (1 - costs["total_value"] / costs["total_cost"]) if costs["total_cost"] > 0 else 0
            })

        # Check for expensive models being overused
        for model, stats in costs.get("by_model", {}).items():
            if "opus" in model.lower() and stats["cost"] > 10:
                recommendations.append({
                    "priority": "high",
                    "issue": f"Opus model costing ${stats['cost']:.2f}",
                    "action": "Switch to Sonnet for most tasks (5x cheaper)",
                    "savings_potential": stats["cost"] * 0.8
                })

        # Check non-value-generating purposes
        for purpose, stats in costs.get("by_purpose", {}).items():
            if "test" in purpose.lower() or "debug" in purpose.lower():
                if stats["cost"] > 5:
                    recommendations.append({
                        "priority": "medium",
                        "issue": f"${stats['cost']:.2f} spent on '{purpose}'",
                        "action": "Eliminate non-production API usage",
                        "savings_potential": stats["cost"]
                    })

        # Free tier maximization
        recommendations.append({
            "priority": "info",
            "issue": "Free tier optimization",
            "action": "Use Claude CLI subscription ($20 fixed) for research. Reserve API for automated signals.",
            "savings_potential": 0
        })

        return recommendations

    def budget_status(self) -> Dict:
        """Get current budget status"""
        costs = self.get_period_costs(30)

        # Calculate days into month
        now = datetime.utcnow()
        days_in_month = 30
        days_elapsed = now.day

        # Pro-rate budget
        prorated_budget = MONTHLY_BUDGET_USD * (days_elapsed / days_in_month)

        roi_pct = costs.get("roi_pct", 0.0)

        return {
            "monthly_budget": MONTHLY_BUDGET_USD,
            "prorated_budget": round(prorated_budget, 2),
            "spent": round(costs.get("total_cost", 0), 2),
            "remaining": round(prorated_budget - costs.get("total_cost", 0), 2),
            "value_generated": round(costs.get("total_value", 0), 2),
            "roi_pct": round(roi_pct, 1),
            "on_track": costs.get("total_cost", 0) <= prorated_budget,
            "profitable": roi_pct >= 100
        }


def generate_cost_strategy():
    """Generate the optimal cost strategy given current situation"""

    strategy = {
        "context": {
            "runway_months": 0.8,
            "monthly_ai_spend": 250,
            "critical": "Every AI call must generate value"
        },
        "fixed_costs": {
            "claude_max": {"monthly": 20, "roi_strategy": "Use for all research/exploration (unlimited)"},
            "chatgpt_plus": {"monthly": 20, "roi_strategy": "Use for market research (unlimited)"},
            "copilot_pro": {"monthly": 10, "roi_strategy": "Code assistance (already integrated)"}
        },
        "variable_costs": {
            "anthropic_api": {
                "budget": 100,
                "purpose": "Trading signal generation ONLY",
                "target_roi": "200%+ (every $1 API cost should generate $2+ in trading profits)"
            },
            "openrouter": {
                "budget": 50,
                "purpose": "Fallback when Anthropic hits limits"
            },
            "other": {
                "budget": 50,
                "purpose": "Strict necessity only"
            }
        },
        "optimization_rules": [
            "NEVER use Opus for routine tasks (5x cost of Sonnet)",
            "Batch similar requests to reduce API calls",
            "Cache common queries (don't re-ask same questions)",
            "Use Claude CLI subscription for exploration (it's unlimited)",
            "Reserve API budget exclusively for trading signals",
            "Track ROI on every API call - cut negative ROI usage"
        ],
        "target_economics": {
            "monthly_ai_cost": 250,
            "required_trading_profit_to_break_even": 250,
            "target_trading_profit": 500,  # 2x ROI
            "min_trades_per_month": 50,
            "avg_profit_per_trade": 10  # Requires good edge
        }
    }

    return strategy


if __name__ == "__main__":
    print("=" * 60)
    print("AI COST OPTIMIZER")
    print("=" * 60)
    print()

    optimizer = AICostOptimizer()

    # Generate strategy
    strategy = generate_cost_strategy()
    print("COST STRATEGY:")
    print(f"  Runway: {strategy['context']['runway_months']} months")
    print(f"  Monthly AI Spend: ${strategy['context']['monthly_ai_spend']}")
    print()

    print("FIXED COSTS (subscriptions):")
    for name, data in strategy['fixed_costs'].items():
        print(f"  {name}: ${data['monthly']}/mo - {data['roi_strategy']}")
    print()

    print("VARIABLE COSTS (pay-per-use):")
    for name, data in strategy['variable_costs'].items():
        print(f"  {name}: ${data['budget']}/mo - {data['purpose']}")
    print()

    print("OPTIMIZATION RULES:")
    for rule in strategy['optimization_rules']:
        print(f"  • {rule}")
    print()

    print("TARGET ECONOMICS:")
    for key, value in strategy['target_economics'].items():
        print(f"  {key}: {value}")
    print()

    # Get recommendations
    recs = optimizer.optimize_recommendations()
    if recs:
        print("RECOMMENDATIONS:")
        for rec in recs:
            print(f"  [{rec['priority'].upper()}] {rec['issue']}")
            print(f"    Action: {rec['action']}")
            if rec.get('savings_potential', 0) > 0:
                print(f"    Potential savings: ${rec['savings_potential']:.2f}")
    print()

    # Budget status
    status = optimizer.budget_status()
    print("BUDGET STATUS:")
    print(f"  Monthly budget: ${status['monthly_budget']}")
    print(f"  Spent so far: ${status['spent']}")
    print(f"  Value generated: ${status['value_generated']}")
    print(f"  ROI: {status['roi_pct']}%")
    print(f"  On track: {'✅' if status['on_track'] else '❌'}")
    print(f"  Profitable: {'✅' if status['profitable'] else '❌'}")
