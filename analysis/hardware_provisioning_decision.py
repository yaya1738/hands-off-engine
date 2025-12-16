#!/usr/bin/env python3
"""
Hardware Provisioning Decision Analysis
========================================

Uses ABCFC to determine optimal hardware for next base.
Comprehensive analysis of all options.

Master: Yair Siegel
"""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class HardwareOption:
    """Hardware option for analysis."""
    name: str
    provider: str
    cpu_cores: int
    ram_gb: float
    storage_gb: int
    bandwidth_tb: float
    cost_per_month: float
    setup_time_hours: float
    geographic_locations: List[str]
    free_tier: bool
    free_tier_duration_months: int


def abcfc_score(
    expected_value: float,
    probability: float,
    cost: float,
    risk_aversion: float = 0.3
) -> float:
    """Calculate ABCFC score."""
    expected = expected_value * probability
    risk = risk_aversion * cost * (1 - probability)
    return expected - risk


def analyze_hardware_options():
    """Analyze all hardware options comprehensively."""

    print("=" * 80)
    print("🖥️  HARDWARE PROVISIONING ANALYSIS")
    print("=" * 80)
    print()

    # Define all options
    options = [
        HardwareOption(
            name="Oracle Cloud - Always Free",
            provider="oracle",
            cpu_cores=1,
            ram_gb=1.0,
            storage_gb=50,
            bandwidth_tb=10.0,
            cost_per_month=0.0,
            setup_time_hours=0.5,
            geographic_locations=["US-Phoenix", "US-Ashburn", "Frankfurt", "London"],
            free_tier=True,
            free_tier_duration_months=999  # Forever free
        ),
        HardwareOption(
            name="AWS EC2 t2.micro",
            provider="aws",
            cpu_cores=1,
            ram_gb=1.0,
            storage_gb=30,
            bandwidth_tb=0.1,
            cost_per_month=0.0,  # Free tier
            setup_time_hours=0.5,
            geographic_locations=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            free_tier=True,
            free_tier_duration_months=12
        ),
        HardwareOption(
            name="GCP e2-micro",
            provider="gcp",
            cpu_cores=2,
            ram_gb=1.0,
            storage_gb=30,
            bandwidth_tb=0.1,
            cost_per_month=0.0,  # Free tier
            setup_time_hours=0.5,
            geographic_locations=["us-central1", "us-east1", "europe-west1", "asia-east1"],
            free_tier=True,
            free_tier_duration_months=12
        ),
        HardwareOption(
            name="Hetzner CX11",
            provider="hetzner",
            cpu_cores=1,
            ram_gb=2.0,
            storage_gb=20,
            bandwidth_tb=20.0,
            cost_per_month=3.79,
            setup_time_hours=0.25,
            geographic_locations=["Nuremberg", "Helsinki", "Falkenstein"],
            free_tier=False,
            free_tier_duration_months=0
        ),
        HardwareOption(
            name="DigitalOcean Basic",
            provider="digitalocean",
            cpu_cores=1,
            ram_gb=1.0,
            storage_gb=25,
            bandwidth_tb=1.0,
            cost_per_month=4.0,
            setup_time_hours=0.25,
            geographic_locations=["NYC", "SFO", "LON", "FRA", "SGP"],
            free_tier=False,
            free_tier_duration_months=0
        ),
        HardwareOption(
            name="Termux (Android)",
            provider="termux",
            cpu_cores=4,  # Modern phone
            ram_gb=2.0,
            storage_gb=10,
            bandwidth_tb=0.0,  # Mobile data limits
            cost_per_month=0.0,
            setup_time_hours=1.0,
            geographic_locations=["Local"],
            free_tier=True,
            free_tier_duration_months=999
        )
    ]

    # System requirements
    print("📋 SYSTEM REQUIREMENTS:")
    print("-" * 80)
    print("  Minimum CPU: 1 core")
    print("  Minimum RAM: 512 MB (1GB recommended)")
    print("  Storage: ~5GB (logs, state, code)")
    print("  Bandwidth: Low (<1GB/day)")
    print("  Uptime: 24/7")
    print("  Geographic: Any (prefer US/EU for latency)")
    print()

    # Value analysis
    print("💰 VALUE ANALYSIS:")
    print("-" * 80)
    print("  Redundancy Value: $1000/month")
    print("    (If primary fails, backup prevents $1000 loss)")
    print("  Primary Failure Probability: 5%/month")
    print("  Expected Value: $1000 × 0.05 = $50/month")
    print()

    # Score each option
    print("🎯 ABCFC SCORING:")
    print("=" * 80)

    scored_options = []

    for option in options:
        # Calculate expected value (redundancy value if primary fails)
        redundancy_value = 1000.0
        failure_probability = 0.05

        # Cost includes monthly cost and setup time cost
        setup_cost = option.setup_time_hours * 10  # $10/hour for setup time
        monthly_cost = option.cost_per_month

        # Amortize setup cost over 12 months
        total_monthly_cost = monthly_cost + (setup_cost / 12)

        # ABCFC score
        score = abcfc_score(
            expected_value=redundancy_value,
            probability=failure_probability,
            cost=total_monthly_cost,
            risk_aversion=0.3
        )

        # Bonus for free tier
        if option.free_tier:
            score += 20

        # Bonus for more locations
        score += len(option.geographic_locations) * 2

        # Bonus for better specs
        if option.ram_gb >= 2.0:
            score += 10
        if option.bandwidth_tb >= 10.0:
            score += 5

        scored_options.append({
            "option": option,
            "score": score,
            "total_monthly_cost": total_monthly_cost
        })

    # Sort by score
    scored_options.sort(key=lambda x: x["score"], reverse=True)

    # Display results
    for i, item in enumerate(scored_options, 1):
        opt = item["option"]
        score = item["score"]
        cost = item["total_monthly_cost"]

        print(f"\n{i}. {opt.name}")
        print(f"   Provider: {opt.provider}")
        print(f"   Specs: {opt.cpu_cores} CPU, {opt.ram_gb}GB RAM, {opt.storage_gb}GB storage")
        print(f"   Cost: ${cost:.2f}/month")
        if opt.free_tier:
            if opt.free_tier_duration_months > 100:
                print(f"   Free Tier: FOREVER FREE ✨")
            else:
                print(f"   Free Tier: {opt.free_tier_duration_months} months")
        print(f"   Setup Time: {opt.setup_time_hours}h")
        print(f"   Locations: {len(opt.geographic_locations)} ({', '.join(opt.geographic_locations[:3])})")
        print(f"   ABCFC Score: {score:.2f}")

    print()
    print("=" * 80)

    # Recommendation
    best = scored_options[0]
    print("🏆 RECOMMENDATION:")
    print("=" * 80)
    print(f"✅ {best['option'].name}")
    print()
    print("REASONING:")
    if best['option'].cost_per_month == 0:
        print("  • ZERO cost (infinite ROI)")
    if best['option'].free_tier and best['option'].free_tier_duration_months > 100:
        print("  • Forever free (no expiration)")
    print(f"  • {best['option'].ram_gb}GB RAM (sufficient for our needs)")
    print(f"  • {len(best['option'].geographic_locations)} geographic locations")
    print(f"  • Setup time: {best['option'].setup_time_hours}h")
    print(f"  • ABCFC Score: {best['score']:.2f} (highest)")
    print()

    print("NEXT STEPS:")
    print(f"  1. Create {best['option'].provider} account")
    print(f"  2. Provision instance in optimal location")
    print(f"  3. Run setup script")
    print(f"  4. Deploy system")
    print()

    # Save analysis
    result = {
        "timestamp": "2025-12-04T22:30:00Z",
        "recommendation": {
            "name": best['option'].name,
            "provider": best['option'].provider,
            "score": best['score'],
            "cost_per_month": best['total_monthly_cost'],
            "specs": {
                "cpu_cores": best['option'].cpu_cores,
                "ram_gb": best['option'].ram_gb,
                "storage_gb": best['option'].storage_gb
            }
        },
        "all_options": [
            {
                "name": item['option'].name,
                "score": item['score'],
                "cost": item['total_monthly_cost']
            }
            for item in scored_options
        ]
    }

    with open("/root/hands-off-engine/analysis/hardware_decision.json", "w") as f:
        json.dump(result, f, indent=2)

    print("📊 Analysis saved to: analysis/hardware_decision.json")
    print()

    return best['option']


if __name__ == "__main__":
    analyze_hardware_options()
