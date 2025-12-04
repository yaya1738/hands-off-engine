#!/usr/bin/env python3
"""
Decision Chaos Analysis
========================

ABCFC analysis for autonomous income strategy decisions.
Determines optimal next move from multiple options.

Master: Yair Siegel
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent


def abcfc_score(
    expected_value: float,
    probability: float,
    worst_case: float,
    risk_aversion: float = 0.3
) -> float:
    """
    Component-level ABCFC scoring.

    Score = (expected_value × probability) - (risk_aversion × |worst_case| × (1 - probability))
    """
    expected = expected_value * probability
    risk = risk_aversion * abs(worst_case) * (1 - probability)
    return expected - risk


def analyze_option(
    name: str,
    expected_value: float,
    probability: float,
    time_cost_hours: float,
    worst_case: float,
    details: str
) -> Dict:
    """Analyze a single decision option."""

    # Calculate ABCFC score
    score = abcfc_score(expected_value, probability, worst_case)

    # Expected hourly rate
    hourly_rate = (expected_value * probability) / max(time_cost_hours, 1) if time_cost_hours > 0 else 0

    # Risk-adjusted value
    risk_adjusted = expected_value * probability + worst_case * (1 - probability)

    return {
        "name": name,
        "expected_value": expected_value,
        "probability": probability,
        "time_cost_hours": time_cost_hours,
        "worst_case": worst_case,
        "abcfc_score": score,
        "hourly_rate": hourly_rate,
        "risk_adjusted_value": risk_adjusted,
        "details": details
    }


def main():
    """Run decision chaos analysis."""

    print("=" * 80)
    print("DECISION CHAOS ANALYSIS - AUTONOMOUS INCOME STRATEGY")
    print("=" * 80)
    print()

    # Define options
    options = [
        analyze_option(
            name="Option 1: Expand Bounty Scanning (10x sources)",
            expected_value=1500,  # Finding 1-2 bounties worth $1-2k
            probability=0.30,  # 30% chance of finding unclaimed bounties
            time_cost_hours=3,  # 2-3 hours to expand scanner
            worst_case=-3 * 30,  # 3 hours × $30/hr opportunity cost
            details="Scan 100+ GitHub repos, GitLab, dev boards. High volume, low conversion."
        ),
        analyze_option(
            name="Option 2: Compete on Open PRs",
            expected_value=1750,  # Average of $1,500-2,000
            probability=0.20,  # 20% chance (risky - PR might get merged first, maintainer rejection)
            time_cost_hours=15,  # 10-20 hours per implementation
            worst_case=-15 * 30 - 50,  # Time cost + reputation damage
            details="Build better implementation for dojo-spas open PRs. High risk of rejection/waste."
        ),
        analyze_option(
            name="Option 3: Create New Income Stream",
            expected_value=5000,  # Potential long-term value
            probability=0.15,  # 15% chance of success (high uncertainty)
            time_cost_hours=40,  # Days/weeks of work
            worst_case=-40 * 30,  # Pure time loss
            details="Build novel autonomous service/tool. High upside, high uncertainty, high time cost."
        ),
        analyze_option(
            name="Option 4: Scale Money Printer",
            expected_value=500,  # Incremental gains from more capital/markets
            probability=0.60,  # 60% chance (proven strategy)
            time_cost_hours=2,  # Quick parameter tweaks
            worst_case=-200,  # Potential losses from aggressive trading
            details="Optimize existing Money Printer. Low time cost, proven strategy, moderate upside."
        ),
        analyze_option(
            name="Option 5: Hybrid - Scan + Scale Money Printer",
            expected_value=2000,  # Combined value
            probability=0.45,  # Better odds than pure scanning
            time_cost_hours=5,  # Both tasks combined
            worst_case=-200,  # Worst case is trading losses
            details="Expand bounty scanner + optimize Money Printer in parallel. Best of both worlds."
        ),
    ]

    # Sort by ABCFC score (descending)
    options.sort(key=lambda x: x["abcfc_score"], reverse=True)

    print("📊 RANKED OPTIONS (by ABCFC Score):")
    print("-" * 80)
    print()

    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt['name']}")
        print(f"   ABCFC Score: {opt['abcfc_score']:.2f}")
        print(f"   Expected Value: ${opt['expected_value']:,.0f}")
        print(f"   Probability: {opt['probability']:.0%}")
        print(f"   Time Cost: {opt['time_cost_hours']:.1f} hours")
        print(f"   Worst Case: ${opt['worst_case']:.0f}")
        print(f"   Hourly Rate: ${opt['hourly_rate']:.2f}/hr")
        print(f"   Risk-Adjusted Value: ${opt['risk_adjusted_value']:.2f}")
        print(f"   Details: {opt['details']}")
        print()

    print("=" * 80)
    print("🎯 RECOMMENDATION")
    print("=" * 80)
    print()

    winner = options[0]
    print(f"**{winner['name']}**")
    print()
    print(f"Score: {winner['abcfc_score']:.2f}")
    print(f"Hourly Rate: ${winner['hourly_rate']:.2f}/hr")
    print()
    print("Reasoning:")
    if winner['name'].startswith("Option 5"):
        print("- Combines proven Money Printer strategy (60% success rate)")
        print("- Adds low-cost bounty scanning (30% find rate)")
        print("- Minimal time investment (5 hours)")
        print("- Diversified risk across two income streams")
        print("- Best risk-adjusted returns")
    elif winner['name'].startswith("Option 4"):
        print("- Proven strategy with 60% success rate")
        print("- Minimal time investment (2 hours)")
        print("- Low downside risk")
        print("- Immediate execution possible")
    elif winner['name'].startswith("Option 1"):
        print("- Low time cost (3 hours)")
        print("- Scalable scanning approach")
        print("- Reasonable probability (30%)")
        print("- Sets up future opportunities")

    print()
    print("=" * 80)

    # Save analysis
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "options": options,
        "winner": winner,
        "methodology": "Component ABCFC with risk aversion = 0.3"
    }

    output_file = PROJECT_ROOT / "state" / "decision_analysis.json"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2))

    print(f"Analysis saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
