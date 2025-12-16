#!/usr/bin/env python3
"""
High-Performance Hardware Analysis
===================================

Analyzing POWERFUL compute options for primary Base 2.
Free tier can be "additives" but main base needs serious compute.

Master: Yair Siegel
"""

import json
from dataclasses import dataclass


@dataclass
class HighPerfOption:
    """High-performance hardware option."""
    name: str
    provider: str
    cpu_cores: int
    ram_gb: float
    storage_gb: int
    bandwidth_tb: float
    cost_per_month: float
    gpu: bool
    setup_time_hours: float
    autonomy_level: float  # Can system provision it autonomously?


def abcfc_score(expected_value: float, probability: float, cost: float) -> float:
    """Calculate ABCFC score."""
    expected = expected_value * probability
    risk = 0.3 * cost * (1 - probability)
    return expected - risk


def analyze_high_performance():
    """Analyze high-performance options."""

    print("=" * 80)
    print("💪 HIGH-PERFORMANCE COMPUTE ANALYSIS")
    print("=" * 80)
    print()
    print("Goal: STRONG compute for primary Base 2")
    print("Secondary: Free tier as supplementary additions")
    print()

    # High-performance options
    options = [
        HighPerfOption(
            name="Oracle Cloud - ARM Ampere A1 (Always Free)",
            provider="oracle",
            cpu_cores=4,
            ram_gb=24.0,
            storage_gb=200,
            bandwidth_tb=10.0,
            cost_per_month=0.0,  # Forever free!
            gpu=False,
            setup_time_hours=0.5,
            autonomy_level=0.2  # Web console
        ),
        HighPerfOption(
            name="Hetzner CPX31",
            provider="hetzner",
            cpu_cores=4,
            ram_gb=8.0,
            storage_gb=160,
            bandwidth_tb=20.0,
            cost_per_month=13.90,
            gpu=False,
            setup_time_hours=0.05,
            autonomy_level=0.98  # API
        ),
        HighPerfOption(
            name="Hetzner CCX13",
            provider="hetzner",
            cpu_cores=2,  # Dedicated AMD EPYC
            ram_gb=8.0,
            storage_gb=80,
            bandwidth_tb=20.0,
            cost_per_month=29.90,
            gpu=False,
            setup_time_hours=0.05,
            autonomy_level=0.98  # API
        ),
        HighPerfOption(
            name="DigitalOcean Performance - 4vCPU",
            provider="digitalocean",
            cpu_cores=4,
            ram_gb=8.0,
            storage_gb=100,
            bandwidth_tb=5.0,
            cost_per_month=48.0,
            gpu=False,
            setup_time_hours=0.05,
            autonomy_level=0.98  # API
        ),
        HighPerfOption(
            name="AWS EC2 t3.large",
            provider="aws",
            cpu_cores=2,
            ram_gb=8.0,
            storage_gb=50,
            bandwidth_tb=0.1,
            cost_per_month=60.74,  # ~$0.0832/hr * 730hr
            gpu=False,
            setup_time_hours=0.1,
            autonomy_level=0.95  # CLI
        ),
        HighPerfOption(
            name="Hetzner AX41-NVMe (Dedicated)",
            provider="hetzner",
            cpu_cores=8,  # AMD Ryzen 7 3700X
            ram_gb=64.0,
            storage_gb=1024,  # 2x 512GB NVMe
            bandwidth_tb=20.0,
            cost_per_month=49.90,
            gpu=False,
            setup_time_hours=24.0,  # Dedicated server setup
            autonomy_level=0.90  # Mostly automated
        ),
        HighPerfOption(
            name="Vast.ai GPU Instance",
            provider="vastai",
            cpu_cores=8,
            ram_gb=32.0,
            storage_gb=100,
            bandwidth_tb=1.0,
            cost_per_month=30.0,  # ~$0.04/hr
            gpu=True,
            setup_time_hours=0.1,
            autonomy_level=0.95  # CLI
        )
    ]

    print("📊 REQUIREMENTS ANALYSIS:")
    print("-" * 80)
    print("  For full autonomous system with heavy compute:")
    print("  • Minimum: 4 CPU cores, 8GB RAM")
    print("  • Recommended: 8+ CPU cores, 16GB+ RAM")
    print("  • Storage: 100GB+ for logs/state/repos")
    print("  • Immediate provisioning preferred")
    print()

    # Score each
    scored = []

    for opt in options:
        # Value increases with compute power
        compute_value = (opt.cpu_cores * 10) + (opt.ram_gb * 5)

        # Expected value from having powerful base
        expected_value = 100 + compute_value  # Base + compute bonus

        # Probability of success
        probability = 0.95

        # ABCFC base score
        base_score = abcfc_score(expected_value, probability, opt.cost_per_month)

        # Autonomy bonus
        autonomy_bonus = opt.autonomy_level * 30

        # Immediate availability bonus
        if opt.setup_time_hours < 1:
            speed_bonus = 20
        elif opt.setup_time_hours < 2:
            speed_bonus = 10
        else:
            speed_bonus = 0

        # GPU bonus
        gpu_bonus = 15 if opt.gpu else 0

        # Dedicated hardware bonus
        dedicated_bonus = 10 if opt.ram_gb >= 16 else 0

        final_score = (base_score + autonomy_bonus + speed_bonus +
                      gpu_bonus + dedicated_bonus)

        scored.append({
            "option": opt,
            "base_score": base_score,
            "autonomy_bonus": autonomy_bonus,
            "speed_bonus": speed_bonus,
            "gpu_bonus": gpu_bonus,
            "dedicated_bonus": dedicated_bonus,
            "final_score": final_score,
            "compute_power": opt.cpu_cores * opt.ram_gb
        })

    # Sort by score
    scored.sort(key=lambda x: x["final_score"], reverse=True)

    print("🎯 HIGH-PERFORMANCE OPTIONS RANKED:")
    print("=" * 80)

    for i, item in enumerate(scored, 1):
        opt = item["option"]

        print(f"\n{i}. {opt.name}")
        print(f"   Provider: {opt.provider}")
        print(f"   Specs: {opt.cpu_cores} CPU, {opt.ram_gb}GB RAM, {opt.storage_gb}GB storage")
        if opt.gpu:
            print(f"   GPU: ✅ YES")
        print(f"   Cost: ${opt.cost_per_month:.2f}/month")
        print(f"   Setup: {opt.setup_time_hours}h")
        print(f"   Autonomy: {opt.autonomy_level:.0%}")
        print(f"   Compute Power: {item['compute_power']:.0f} (CPU×RAM)")
        print()
        print(f"   Scoring:")
        print(f"     Base ABCFC: {item['base_score']:.2f}")
        print(f"     Autonomy: +{item['autonomy_bonus']:.2f}")
        print(f"     Speed: +{item['speed_bonus']:.2f}")
        if item['gpu_bonus'] > 0:
            print(f"     GPU: +{item['gpu_bonus']:.2f}")
        if item['dedicated_bonus'] > 0:
            print(f"     Dedicated: +{item['dedicated_bonus']:.2f}")
        print(f"     FINAL SCORE: {item['final_score']:.2f}")

    print()
    print("=" * 80)

    # Decision
    best = scored[0]
    opt = best["option"]

    print("🏆 PRIMARY BASE RECOMMENDATION")
    print("=" * 80)
    print(f"✅ {opt.name}")
    print()
    print("SPECS:")
    print(f"  • {opt.cpu_cores} CPU cores")
    print(f"  • {opt.ram_gb}GB RAM")
    print(f"  • {opt.storage_gb}GB storage")
    if opt.gpu:
        print(f"  • GPU acceleration")
    print()
    print("ECONOMICS:")
    print(f"  • Cost: ${opt.cost_per_month:.2f}/month")
    if opt.cost_per_month == 0:
        print(f"  • ROI: ∞ (FREE FOREVER)")
    else:
        expected_monthly = 100 + (opt.cpu_cores * 10) + (opt.ram_gb * 5)
        roi = expected_monthly / opt.cost_per_month if opt.cost_per_month > 0 else float('inf')
        print(f"  • Expected value: ${expected_monthly:.2f}/month")
        print(f"  • ROI: {roi:.1f}x")
    print()
    print("PROVISIONING:")
    print(f"  • Setup time: {opt.setup_time_hours}h")
    print(f"  • Autonomy: {opt.autonomy_level:.0%}")
    if opt.autonomy_level >= 0.90:
        print(f"  • ✅ Can provision autonomously")
    else:
        print(f"  • ⚠️  Requires manual setup")
    print()
    print(f"FINAL SCORE: {best['final_score']:.2f}")
    print()

    # Free tier additions
    print("=" * 80)
    print("➕ FREE TIER ADDITIONS (Supplementary)")
    print("=" * 80)
    print()
    print("Add these as extra redundancy (all $0/month):")
    print()
    print("1. Oracle Cloud x86 (1 CPU, 1GB RAM) - Forever free")
    print("2. AWS EC2 t2.micro (1 CPU, 1GB RAM) - 12 months free")
    print("3. GCP e2-micro (2 CPU, 1GB RAM) - 12 months free")
    print()
    print("These supplement the main base for redundancy at zero cost.")
    print()

    # Save decision
    result = {
        "timestamp": "2025-12-04T22:55:00Z",
        "analysis_type": "high_performance",
        "primary_recommendation": {
            "name": opt.name,
            "provider": opt.provider,
            "cpu_cores": opt.cpu_cores,
            "ram_gb": opt.ram_gb,
            "cost_per_month": opt.cost_per_month,
            "score": best["final_score"],
            "autonomy_level": opt.autonomy_level
        },
        "free_tier_supplements": [
            "Oracle Cloud x86 (1 CPU, 1GB RAM)",
            "AWS EC2 t2.micro (1 CPU, 1GB RAM)",
            "GCP e2-micro (2 CPU, 1GB RAM)"
        ],
        "all_options": [
            {
                "name": item["option"].name,
                "cpu": item["option"].cpu_cores,
                "ram_gb": item["option"].ram_gb,
                "cost": item["option"].cost_per_month,
                "score": item["final_score"]
            }
            for item in scored
        ]
    }

    with open("/root/hands-off-engine/analysis/high_performance_decision.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Decision saved to: analysis/high_performance_decision.json")
    print()

    return opt


if __name__ == "__main__":
    analyze_high_performance()
