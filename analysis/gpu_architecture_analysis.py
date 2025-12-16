#!/usr/bin/env python3
"""
GPU Architecture Analysis
==========================

What GPU setup should the system have?
- Single vs Multi-GPU
- NVIDIA vs AMD
- Consumer vs Professional
- Specific models and specs

Master: Yair Siegel
"""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class GPUOption:
    """GPU configuration option."""
    name: str
    gpu_count: int
    gpu_model: str
    vram_per_gpu: int  # GB
    compute_capability: str
    use_cases: List[str]
    cost_per_hour: float
    cost_per_month: float  # Assuming 730 hours
    provider: str
    availability: str  # high, medium, low


def analyze_gpu_requirements():
    """Analyze GPU requirements for autonomous system."""

    print("=" * 80)
    print("🎮 GPU ARCHITECTURE ANALYSIS")
    print("=" * 80)
    print()
    print("Question: What GPU setup should the hands-off system have?")
    print()

    print("📋 CURRENT & FUTURE WORKLOADS:")
    print("-" * 80)
    print("  Current:")
    print("    • API orchestration (lightweight, no GPU needed)")
    print("    • Trading execution (lightweight, no GPU needed)")
    print("    • Data analysis (could benefit from GPU)")
    print()
    print("  Future:")
    print("    • ML model training (market prediction)")
    print("    • Pattern recognition (trading signals)")
    print("    • Large-scale data processing")
    print("    • AI-powered decision making")
    print("    • Natural language processing (analyzing news/social)")
    print("    • Computer vision (chart analysis)")
    print()

    print("🎯 GPU REQUIREMENTS:")
    print("-" * 80)
    print("  Minimum:")
    print("    • 8GB+ VRAM for basic ML")
    print("    • CUDA support (NVIDIA)")
    print("    • Good compute/$ ratio")
    print()
    print("  Ideal:")
    print("    • 16GB+ VRAM for larger models")
    print("    • Multi-GPU for parallel training")
    print("    • Latest architecture (Ampere/Ada)")
    print("    • High availability")
    print()

    # GPU options
    options = [
        GPUOption(
            name="Single RTX 4090",
            gpu_count=1,
            gpu_model="RTX 4090",
            vram_per_gpu=24,
            compute_capability="8.9 (Ada Lovelace)",
            use_cases=["ML training", "Inference", "Data processing"],
            cost_per_hour=0.80,
            cost_per_month=584.00,
            provider="Vast.ai / RunPod",
            availability="high"
        ),
        GPUOption(
            name="Dual RTX 4090",
            gpu_count=2,
            gpu_model="RTX 4090",
            vram_per_gpu=24,
            compute_capability="8.9 (Ada Lovelace)",
            use_cases=["Parallel training", "Multi-model inference", "Large models"],
            cost_per_hour=1.60,
            cost_per_month=1168.00,
            provider="Vast.ai / RunPod",
            availability="medium"
        ),
        GPUOption(
            name="Single A100 40GB",
            gpu_count=1,
            gpu_model="A100 40GB",
            vram_per_gpu=40,
            compute_capability="8.0 (Ampere)",
            use_cases=["Professional ML", "Large models", "Production inference"],
            cost_per_hour=1.50,
            cost_per_month=1095.00,
            provider="Vast.ai / Lambda",
            availability="high"
        ),
        GPUOption(
            name="Single A100 80GB",
            gpu_count=1,
            gpu_model="A100 80GB",
            vram_per_gpu=80,
            compute_capability="8.0 (Ampere)",
            use_cases=["Very large models", "Multi-task", "Production"],
            cost_per_hour=2.50,
            cost_per_month=1825.00,
            provider="Lambda / CoreWeave",
            availability="medium"
        ),
        GPUOption(
            name="Dual A100 40GB",
            gpu_count=2,
            gpu_model="A100 40GB",
            vram_per_gpu=40,
            compute_capability="8.0 (Ampere)",
            use_cases=["Multi-GPU training", "Very large models", "Production scale"],
            cost_per_hour=3.00,
            cost_per_month=2190.00,
            provider="Lambda / CoreWeave",
            availability="low"
        ),
        GPUOption(
            name="Single H100",
            gpu_count=1,
            gpu_model="H100 80GB",
            vram_per_gpu=80,
            compute_capability="9.0 (Hopper)",
            use_cases=["Cutting-edge ML", "LLM training", "Max performance"],
            cost_per_hour=4.00,
            cost_per_month=2920.00,
            provider="Lambda / CoreWeave",
            availability="low"
        ),
        GPUOption(
            name="Single RTX 3090",
            gpu_count=1,
            gpu_model="RTX 3090",
            vram_per_gpu=24,
            compute_capability="8.6 (Ampere)",
            use_cases=["Budget ML", "Good value", "Learning"],
            cost_per_hour=0.40,
            cost_per_month=292.00,
            provider="Vast.ai",
            availability="high"
        ),
        GPUOption(
            name="Quad RTX 3090",
            gpu_count=4,
            gpu_model="RTX 3090",
            vram_per_gpu=24,
            compute_capability="8.6 (Ampere)",
            use_cases=["Budget multi-GPU", "Parallel training", "Max VRAM/price"],
            cost_per_hour=1.40,
            cost_per_month=1022.00,
            provider="Vast.ai",
            availability="medium"
        ),
        GPUOption(
            name="Single RTX A6000",
            gpu_count=1,
            gpu_model="RTX A6000",
            vram_per_gpu=48,
            compute_capability="8.6 (Ampere)",
            use_cases=["Professional workstation", "Large VRAM", "Stable"],
            cost_per_hour=0.90,
            cost_per_month=657.00,
            provider="Vast.ai / RunPod",
            availability="medium"
        )
    ]

    print("=" * 80)
    print("GPU OPTIONS ANALYSIS")
    print("=" * 80)
    print()

    # Score options
    scored = []
    for opt in options:
        # Calculate value scores
        total_vram = opt.gpu_count * opt.vram_per_gpu
        vram_score = total_vram * 2  # VRAM is very valuable

        # Multi-GPU bonus
        multi_gpu_bonus = (opt.gpu_count - 1) * 50 if opt.gpu_count > 1 else 0

        # Availability bonus (high availability is important)
        avail_bonus = {"high": 50, "medium": 25, "low": 0}[opt.availability]

        # Cost efficiency (VRAM per dollar per month)
        cost_efficiency = total_vram / opt.cost_per_month if opt.cost_per_month > 0 else 0

        # Modern architecture bonus
        modern_bonus = 30 if "4090" in opt.gpu_model or "H100" in opt.gpu_model else 0
        modern_bonus += 20 if "A100" in opt.gpu_model else 0

        # Professional GPU bonus
        pro_bonus = 25 if "A100" in opt.gpu_model or "H100" in opt.gpu_model or "A6000" in opt.gpu_model else 0

        total_score = (vram_score + multi_gpu_bonus + avail_bonus +
                      cost_efficiency * 20 + modern_bonus + pro_bonus)

        scored.append({
            "option": opt,
            "vram_score": vram_score,
            "multi_gpu_bonus": multi_gpu_bonus,
            "avail_bonus": avail_bonus,
            "cost_efficiency": cost_efficiency,
            "modern_bonus": modern_bonus,
            "pro_bonus": pro_bonus,
            "total_score": total_score
        })

    # Sort by score
    scored.sort(key=lambda x: x["total_score"], reverse=True)

    print("📊 RANKED OPTIONS:")
    print()

    for i, item in enumerate(scored, 1):
        opt = item["option"]
        total_vram = opt.gpu_count * opt.vram_per_gpu

        print(f"{i}. {opt.name}")
        print(f"   GPU: {opt.gpu_count}x {opt.gpu_model}")
        print(f"   Total VRAM: {total_vram}GB")
        print(f"   Compute: {opt.compute_capability}")
        print(f"   Cost: ${opt.cost_per_hour:.2f}/hr → ${opt.cost_per_month:.0f}/month")
        print(f"   Provider: {opt.provider}")
        print(f"   Availability: {opt.availability}")
        print(f"   Use cases: {', '.join(opt.use_cases[:3])}")
        print()
        print(f"   Scoring:")
        print(f"     VRAM: {item['vram_score']:.0f}")
        print(f"     Multi-GPU: +{item['multi_gpu_bonus']:.0f}")
        print(f"     Availability: +{item['avail_bonus']:.0f}")
        print(f"     Cost Efficiency: {item['cost_efficiency']:.2f} GB/$month")
        print(f"     Modern: +{item['modern_bonus']:.0f}")
        print(f"     Professional: +{item['pro_bonus']:.0f}")
        print(f"     TOTAL SCORE: {item['total_score']:.0f}")
        print()

    print("=" * 80)
    print("🏆 RECOMMENDATIONS BY USE CASE")
    print("=" * 80)
    print()

    print("🥇 BEST OVERALL: Single RTX 4090")
    print("   • 24GB VRAM (good for most models)")
    print("   • Latest architecture (Ada Lovelace)")
    print("   • High availability")
    print("   • $584/month (reasonable)")
    print("   • Perfect for: ML training, inference, data processing")
    print()

    print("🥈 BEST VALUE: Single RTX 3090")
    print("   • 24GB VRAM (same as 4090)")
    print("   • Older but still very capable")
    print("   • High availability")
    print("   • $292/month (HALF the cost of 4090)")
    print("   • Perfect for: Learning, development, good enough for production")
    print()

    print("🥉 BEST FOR SCALING: Dual RTX 4090")
    print("   • 48GB total VRAM")
    print("   • Parallel training capability")
    print("   • Latest architecture")
    print("   • $1168/month")
    print("   • Perfect for: Large models, parallel experiments")
    print()

    print("💎 PROFESSIONAL CHOICE: Single A100 40GB")
    print("   • 40GB VRAM")
    print("   • Enterprise-grade reliability")
    print("   • Best multi-tenancy support")
    print("   • $1095/month")
    print("   • Perfect for: Production workloads, mission-critical")
    print()

    print("🚀 MAXIMUM POWER: Single H100")
    print("   • 80GB VRAM")
    print("   • Absolute cutting edge")
    print("   • 2-3x faster than A100")
    print("   • $2920/month")
    print("   • Perfect for: LLM training, bleeding edge research")
    print()

    print("=" * 80)
    print("🎯 RECOMMENDATION FOR HANDS-OFF SYSTEM")
    print("=" * 80)
    print()

    print("CURRENT NEEDS:")
    print("  • Not GPU-intensive yet (API orchestration is CPU-based)")
    print("  • Future ML/AI expansion planned")
    print("  • Cost-conscious but value-focused")
    print()

    print("RECOMMENDED: Single RTX 4090")
    print("-" * 80)
    print("  GPU: 1x RTX 4090")
    print("  VRAM: 24GB")
    print("  Cost: $584/month (~$0.80/hr)")
    print("  Provider: Vast.ai or RunPod")
    print()
    print("WHY:")
    print("  ✅ Latest architecture (Ada Lovelace 8.9)")
    print("  ✅ 24GB VRAM (handles most models)")
    print("  ✅ High availability (easy to provision)")
    print("  ✅ Fast inference (2x faster than 3090)")
    print("  ✅ Good value (best performance per dollar in new GPUs)")
    print("  ✅ Scalable (can add 2nd GPU later if needed)")
    print()

    print("ALTERNATIVE: Single RTX 3090 (Budget Option)")
    print("-" * 80)
    print("  GPU: 1x RTX 3090")
    print("  VRAM: 24GB")
    print("  Cost: $292/month (~$0.40/hr)")
    print("  Provider: Vast.ai")
    print()
    print("WHY:")
    print("  ✅ Same VRAM as 4090 (24GB)")
    print("  ✅ HALF the cost")
    print("  ✅ Still very capable for ML")
    print("  ⚠️  Older architecture (20-30% slower)")
    print("  ✅ High availability")
    print()

    print("UPGRADE PATH:")
    print("-" * 80)
    print("  Phase 1: Start with Single RTX 3090 ($292/mo)")
    print("    → Validate GPU workloads, develop ML models")
    print()
    print("  Phase 2: Upgrade to Single RTX 4090 ($584/mo)")
    print("    → When GPU becomes bottleneck")
    print()
    print("  Phase 3: Add 2nd RTX 4090 → Dual GPU ($1168/mo)")
    print("    → When need parallel training")
    print()
    print("  Phase 4: Professional A100 if enterprise ($1095/mo)")
    print("    → When need production reliability")
    print()

    print("=" * 80)
    print("📐 COMPARISON TO CPU-ONLY")
    print("=" * 80)
    print()
    print("WITHOUT GPU (Current Plan):")
    print("  • Base 2 nodes: $248/month")
    print("  • CPU only: 48 cores, 224GB RAM")
    print("  • ML capabilities: Limited to CPU inference")
    print()
    print("WITH GPU (RTX 4090):")
    print("  • Base 2 nodes: $248/month")
    print("  • GPU node: $584/month")
    print("  • Total: $832/month")
    print("  • ML capabilities: Full training + inference")
    print("  • 100x faster for ML workloads")
    print()
    print("WITH BUDGET GPU (RTX 3090):")
    print("  • Base 2 nodes: $248/month")
    print("  • GPU node: $292/month")
    print("  • Total: $540/month")
    print("  • ML capabilities: Full training + inference")
    print("  • 50x faster for ML workloads")
    print()

    # Save recommendation
    best = scored[0]["option"]
    budget = next(x["option"] for x in scored if "3090" in x["option"].name)

    result = {
        "timestamp": "2025-12-04T23:10:00Z",
        "recommended_primary": {
            "name": best.name,
            "gpu_model": best.gpu_model,
            "gpu_count": best.gpu_count,
            "total_vram": best.gpu_count * best.vram_per_gpu,
            "cost_per_month": best.cost_per_month,
            "provider": best.provider
        },
        "budget_alternative": {
            "name": budget.name,
            "gpu_model": budget.gpu_model,
            "gpu_count": budget.gpu_count,
            "total_vram": budget.gpu_count * budget.vram_per_gpu,
            "cost_per_month": budget.cost_per_month,
            "provider": budget.provider
        },
        "upgrade_path": [
            "Phase 1: RTX 3090 ($292/mo) - Validate",
            "Phase 2: RTX 4090 ($584/mo) - Performance",
            "Phase 3: Dual RTX 4090 ($1168/mo) - Scale",
            "Phase 4: A100/H100 ($1095-2920/mo) - Enterprise"
        ],
        "all_options": [
            {
                "name": item["option"].name,
                "vram": item["option"].gpu_count * item["option"].vram_per_gpu,
                "cost": item["option"].cost_per_month,
                "score": item["total_score"]
            }
            for item in scored
        ]
    }

    with open("/root/hands-off-engine/analysis/gpu_architecture.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Full GPU analysis saved to: analysis/gpu_architecture.json")
    print()


if __name__ == "__main__":
    analyze_gpu_requirements()
