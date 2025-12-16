#!/usr/bin/env python3
"""
Autonomous Provisioning Decision
=================================

What would a fully hands-off system prefer for Base 2?
Analysis from system autonomy perspective.

Master: Yair Siegel
"""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class ProvisioningOption:
    """Provisioning option with autonomy metrics."""
    name: str
    manual_steps_required: int
    time_to_provision_minutes: int
    cost_per_month: float
    autonomy_level: float  # 0.0 to 1.0 (1.0 = fully autonomous)
    expected_value: float
    probability_success: float
    specs_cpu: int
    specs_ram_gb: float
    specs_storage_gb: int


def abcfc_score(expected_value: float, probability: float, cost: float, risk: float = 0.3) -> float:
    """Calculate ABCFC score."""
    expected = expected_value * probability
    risk_penalty = risk * cost * (1 - probability)
    return expected - risk_penalty


def autonomy_bonus(autonomy_level: float) -> float:
    """Bonus for higher autonomy (hands-off preference)."""
    # System strongly prefers autonomous options
    return autonomy_level * 50  # Up to 50 points bonus


def analyze_from_system_perspective():
    """Analyze provisioning options from autonomous system perspective."""

    print("=" * 80)
    print("🤖 AUTONOMOUS SYSTEM TEAM MEETING")
    print("=" * 80)
    print()
    print("Question: What provisioning method does the hands-off system prefer?")
    print()

    options = [
        ProvisioningOption(
            name="Oracle Cloud (Web Console)",
            manual_steps_required=15,  # Account creation, web clicks, etc.
            time_to_provision_minutes=30,
            cost_per_month=0.0,
            autonomy_level=0.2,  # 20% autonomous (mostly manual)
            expected_value=50.0,
            probability_success=0.95,
            specs_cpu=1,
            specs_ram_gb=1.0,
            specs_storage_gb=50
        ),
        ProvisioningOption(
            name="Docker Container (Local)",
            manual_steps_required=0,  # Fully automated
            time_to_provision_minutes=1,
            cost_per_month=0.0,  # Uses existing hardware
            autonomy_level=1.0,  # 100% autonomous
            expected_value=40.0,  # Slightly less (same hardware)
            probability_success=0.99,
            specs_cpu=1,
            specs_ram_gb=2.0,
            specs_storage_gb=20
        ),
        ProvisioningOption(
            name="AWS EC2 (CLI)",
            manual_steps_required=1,  # Just provide credentials once
            time_to_provision_minutes=5,
            cost_per_month=0.0,  # Free tier
            autonomy_level=0.95,  # 95% autonomous
            expected_value=50.0,
            probability_success=0.90,
            specs_cpu=1,
            specs_ram_gb=1.0,
            specs_storage_gb=30
        ),
        ProvisioningOption(
            name="DigitalOcean API",
            manual_steps_required=1,  # API token setup
            time_to_provision_minutes=3,
            cost_per_month=4.0,
            autonomy_level=0.98,  # 98% autonomous
            expected_value=50.0,
            probability_success=0.95,
            specs_cpu=1,
            specs_ram_gb=1.0,
            specs_storage_gb=25
        ),
        ProvisioningOption(
            name="Hetzner API",
            manual_steps_required=1,  # API token setup
            time_to_provision_minutes=2,
            cost_per_month=3.79,
            autonomy_level=0.98,  # 98% autonomous
            expected_value=50.0,
            probability_success=0.95,
            specs_cpu=1,
            specs_ram_gb=2.0,
            specs_storage_gb=20
        )
    ]

    print("📊 ANALYSIS CRITERIA:")
    print("-" * 80)
    print("  Primary: Autonomy level (hands-off preference)")
    print("  Secondary: Cost and specs")
    print("  Tertiary: Provisioning time")
    print()

    # Score each option
    scored_options = []

    for option in options:
        # Base ABCFC score
        time_cost = option.time_to_provision_minutes * 0.1  # $0.10/min of time
        total_cost = option.cost_per_month + time_cost

        base_score = abcfc_score(
            option.expected_value,
            option.probability_success,
            total_cost
        )

        # Autonomy bonus (KEY for hands-off system)
        auto_bonus = autonomy_bonus(option.autonomy_level)

        # Manual steps penalty
        manual_penalty = option.manual_steps_required * 2

        # Quick provisioning bonus
        speed_bonus = max(0, 30 - option.time_to_provision_minutes) * 0.5

        final_score = base_score + auto_bonus + speed_bonus - manual_penalty

        scored_options.append({
            "option": option,
            "base_score": base_score,
            "autonomy_bonus": auto_bonus,
            "manual_penalty": manual_penalty,
            "speed_bonus": speed_bonus,
            "final_score": final_score
        })

    # Sort by final score
    scored_options.sort(key=lambda x: x["final_score"], reverse=True)

    # Display results
    print("🎯 SCORING RESULTS:")
    print("=" * 80)

    for i, item in enumerate(scored_options, 1):
        opt = item["option"]
        score = item["final_score"]

        print(f"\n{i}. {opt.name}")
        print(f"   Autonomy: {opt.autonomy_level:.0%} ({'✅ Fully autonomous' if opt.autonomy_level >= 0.95 else '⚠️  Manual steps required'})")
        print(f"   Manual Steps: {opt.manual_steps_required}")
        print(f"   Provision Time: {opt.time_to_provision_minutes} min")
        print(f"   Cost: ${opt.cost_per_month:.2f}/month")
        print(f"   Specs: {opt.specs_cpu} CPU, {opt.specs_ram_gb}GB RAM, {opt.specs_storage_gb}GB storage")
        print()
        print(f"   Scoring Breakdown:")
        print(f"     Base ABCFC: {item['base_score']:.2f}")
        print(f"     Autonomy Bonus: +{item['autonomy_bonus']:.2f}")
        print(f"     Speed Bonus: +{item['speed_bonus']:.2f}")
        print(f"     Manual Penalty: -{item['manual_penalty']:.2f}")
        print(f"     FINAL SCORE: {score:.2f}")

    print()
    print("=" * 80)

    # Decision
    best = scored_options[0]
    opt = best["option"]

    print("🏆 AUTONOMOUS SYSTEM DECISION")
    print("=" * 80)
    print(f"✅ {opt.name}")
    print()
    print("REASONING:")
    print(f"  • Autonomy level: {opt.autonomy_level:.0%} (system can self-provision)")
    if opt.manual_steps_required == 0:
        print(f"  • Zero manual steps (true hands-off)")
    else:
        print(f"  • Minimal manual steps: {opt.manual_steps_required}")
    print(f"  • Provision time: {opt.time_to_provision_minutes} min (instant)")
    print(f"  • Cost: ${opt.cost_per_month:.2f}/month")
    print(f"  • Final Score: {best['final_score']:.2f} (highest)")
    print()

    print("SYSTEM PERSPECTIVE:")
    print("  As a hands-off autonomous system, I strongly prefer options that")
    print("  require ZERO human interaction. Docker is the most autonomous option.")
    print()

    print("COMPARISON TO HUMAN ANALYSIS:")
    print("  Human analysis chose: Oracle Cloud (Score: 82.88)")
    print("    Reason: Best cost/specs for separate hardware")
    print()
    print(f"  System analysis chose: {opt.name} (Score: {best['final_score']:.2f})")
    print("    Reason: Maximum autonomy (zero manual steps)")
    print()

    print("RECOMMENDATION:")
    if opt.autonomy_level >= 0.95:
        print("  ✅ System can execute this autonomously RIGHT NOW")
        print("     No user interaction needed")
    else:
        print("  ⚠️  Requires user setup first, then system can run autonomously")

    print()

    # Save decision
    result = {
        "timestamp": "2025-12-04T22:50:00Z",
        "perspective": "autonomous_system",
        "decision": {
            "name": opt.name,
            "autonomy_level": opt.autonomy_level,
            "manual_steps": opt.manual_steps_required,
            "provision_time_min": opt.time_to_provision_minutes,
            "cost_per_month": opt.cost_per_month,
            "score": best["final_score"]
        },
        "all_options": [
            {
                "name": item["option"].name,
                "autonomy": item["option"].autonomy_level,
                "score": item["final_score"]
            }
            for item in scored_options
        ]
    }

    with open("/root/hands-off-engine/analysis/autonomous_decision.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Decision saved to: analysis/autonomous_decision.json")
    print()

    return opt


if __name__ == "__main__":
    analyze_from_system_perspective()
