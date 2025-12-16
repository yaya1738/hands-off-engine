#!/usr/bin/env python3
"""
CLEAN SLATE INFRASTRUCTURE ANALYSIS
====================================

Starting from zero: What SHOULD the infrastructure be?

Forget what we currently have. Design optimal setup considering:
- Actual resource needs
- Cost efficiency
- Redundancy requirements
- Geographic distribution
- Provider options (DO, Hetzner, Oracle, AWS, etc.)
- Future scaling (GPU, ML workloads)

Master: Yair Siegel
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class InfrastructureDesign:
    """Complete infrastructure design."""
    name: str
    description: str
    providers: List[str]
    nodes: List[Dict]
    total_monthly_cost: float
    total_vcpus: int
    total_ram_gb: int
    gpus: int
    redundancy_level: int
    regions: int
    abcfc_score: float


def analyze_requirements():
    """Analyze actual requirements from first principles."""

    print("=" * 80)
    print("🎯 CLEAN SLATE INFRASTRUCTURE ANALYSIS")
    print("=" * 80)
    print()

    print("STARTING FROM ZERO: What SHOULD we have?")
    print()

    print("=" * 80)
    print("📊 ACTUAL REQUIREMENTS")
    print("=" * 80)
    print()

    print("WORKLOAD ANALYSIS:")
    print("-" * 80)
    print()

    print("1. TRADING WORKLOADS (Critical - 24/7)")
    print("   • MONEY_PRINTER: 3-4 CPU cores, 4GB RAM")
    print("   • Polymarket trading: 1 CPU, 2GB RAM")
    print("   • Trade executor: 1 CPU, 2GB RAM")
    print("   • Subtotal: ~5 CPU, 8GB RAM")
    print()

    print("2. AUTONOMOUS CORE (Critical - 24/7)")
    print("   • autonomous_loop: 0.5 CPU, 1GB RAM")
    print("   • backend_loop: 0.6 CPU, 1.5GB RAM")
    print("   • api_orchestrator: 0.5 CPU, 1GB RAM")
    print("   • Subtotal: ~1.6 CPU, 3.5GB RAM")
    print()

    print("3. MONITORING/INFRASTRUCTURE (Important)")
    print("   • hardware_brain, scaling_engine, infra_manager, self_healer")
    print("   • Subtotal: ~0.8 CPU, 2GB RAM")
    print()

    print("4. UTILITY SERVICES (Nice to have)")
    print("   • Email handlers, MCP servers")
    print("   • Subtotal: ~1.2 CPU, 2.3GB RAM")
    print()

    print("5. FUTURE ML/AI WORKLOADS (Planned)")
    print("   • GPU compute: RTX 4090 or similar")
    print("   • On-demand usage")
    print()

    print("TOTAL BASELINE: ~8.6 CPU, 15.8GB RAM + GPU (on-demand)")
    print()

    print("=" * 80)
    print("🏗️  INFRASTRUCTURE DESIGN OPTIONS")
    print("=" * 80)
    print()

    designs = []

    # Design 1: Minimal (Single Provider, No Redundancy)
    designs.append(InfrastructureDesign(
        name="Minimal (No Redundancy)",
        description="Absolute minimum - single node, no backup",
        providers=["DigitalOcean"],
        nodes=[
            {"provider": "DigitalOcean", "region": "NYC1", "specs": "8 vCPU, 16GB",
             "role": "ALL-IN-ONE", "cost": 8.0}
        ],
        total_monthly_cost=8.0,
        total_vcpus=8,
        total_ram_gb=16,
        gpus=0,
        redundancy_level=0,
        regions=1,
        abcfc_score=-50.0
    ))

    # Design 2: Basic Redundancy (DO only)
    designs.append(InfrastructureDesign(
        name="Basic Redundancy (DO)",
        description="Primary + Hot Standby, same provider",
        providers=["DigitalOcean"],
        nodes=[
            {"provider": "DigitalOcean", "region": "NYC1", "specs": "8 vCPU, 16GB",
             "role": "PRIMARY", "cost": 8.0},
            {"provider": "DigitalOcean", "region": "NYC1", "specs": "8 vCPU, 16GB",
             "role": "HOT STANDBY", "cost": 8.0}
        ],
        total_monthly_cost=16.0,
        total_vcpus=16,
        total_ram_gb=32,
        gpus=0,
        redundancy_level=1,
        regions=1,
        abcfc_score=100.0
    ))

    # Design 3: Geographic Redundancy (DO Multi-region)
    designs.append(InfrastructureDesign(
        name="Geographic Redundancy (DO)",
        description="Primary (NYC) + Standby (NYC) + EU Backup (Frankfurt)",
        providers=["DigitalOcean"],
        nodes=[
            {"provider": "DigitalOcean", "region": "NYC1", "specs": "8 vCPU, 16GB",
             "role": "PRIMARY", "cost": 8.0},
            {"provider": "DigitalOcean", "region": "NYC1", "specs": "8 vCPU, 16GB",
             "role": "HOT STANDBY", "cost": 8.0},
            {"provider": "DigitalOcean", "region": "Frankfurt", "specs": "4 vCPU, 8GB",
             "role": "EU BACKUP", "cost": 4.0}
        ],
        total_monthly_cost=20.0,
        total_vcpus=20,
        total_ram_gb=40,
        gpus=0,
        redundancy_level=2,
        regions=2,
        abcfc_score=250.0
    ))

    # Design 4: Hybrid Multi-Provider (Hetzner + Oracle + GPU)
    designs.append(InfrastructureDesign(
        name="Hybrid Multi-Provider (OPTIMAL)",
        description="Hetzner (US+EU) + Oracle Free + Vast.ai GPU",
        providers=["Hetzner", "Oracle", "Vast.ai"],
        nodes=[
            {"provider": "Hetzner", "region": "Ashburn US", "specs": "8 CPU, 64GB",
             "role": "PRIMARY", "cost": 49.90},
            {"provider": "Hetzner", "region": "Germany", "specs": "8 CPU, 64GB",
             "role": "HOT STANDBY", "cost": 49.90},
            {"provider": "Oracle", "region": "Phoenix", "specs": "4 CPU, 24GB",
             "role": "FREE BACKUP", "cost": 0.0},
            {"provider": "Vast.ai", "region": "Flexible", "specs": "RTX 4090, 24GB VRAM",
             "role": "GPU (on-demand)", "cost": 292.0}  # Budget: 8hr/day usage
        ],
        total_monthly_cost=391.80,
        total_vcpus=20,
        total_ram_gb=152,
        gpus=1,
        redundancy_level=2,
        regions=3,
        abcfc_score=420.0
    ))

    # Design 5: Cost-Optimized Hybrid
    designs.append(InfrastructureDesign(
        name="Cost-Optimized Hybrid",
        description="Hetzner (US only) + Oracle Free + GPU on-demand",
        providers=["Hetzner", "Oracle", "Vast.ai"],
        nodes=[
            {"provider": "Hetzner", "region": "Ashburn US", "specs": "8 CPU, 64GB",
             "role": "PRIMARY", "cost": 49.90},
            {"provider": "Oracle", "region": "Phoenix", "specs": "4 CPU, 24GB",
             "role": "FREE BACKUP", "cost": 0.0},
            {"provider": "Vast.ai", "region": "Flexible", "specs": "RTX 3090, 24GB VRAM",
             "role": "GPU (occasional)", "cost": 50.0}  # Very light usage
        ],
        total_monthly_cost=99.90,
        total_vcpus=12,
        total_ram_gb=88,
        gpus=1,
        redundancy_level=1,
        regions=2,
        abcfc_score=350.0
    ))

    # Design 6: Maximum Performance (No Budget Constraint)
    designs.append(InfrastructureDesign(
        name="Maximum Performance",
        description="Best hardware, full redundancy, powerful GPU",
        providers=["Hetzner", "Oracle", "Vast.ai"],
        nodes=[
            {"provider": "Hetzner", "region": "Ashburn US", "specs": "16 CPU, 128GB",
             "role": "PRIMARY", "cost": 99.00},
            {"provider": "Hetzner", "region": "Germany", "specs": "16 CPU, 128GB",
             "role": "HOT STANDBY", "cost": 99.00},
            {"provider": "Oracle", "region": "Phoenix", "specs": "4 CPU, 24GB",
             "role": "FREE BACKUP", "cost": 0.0},
            {"provider": "Vast.ai", "region": "Flexible", "specs": "Quad RTX 3090, 96GB VRAM",
             "role": "GPU (24/7)", "cost": 1022.0}
        ],
        total_monthly_cost=1220.0,
        total_vcpus=36,
        total_ram_gb=280,
        gpus=4,
        redundancy_level=2,
        regions=3,
        abcfc_score=500.0
    ))

    # Display designs
    for i, design in enumerate(designs, 1):
        print(f"\n{'=' * 80}")
        print(f"DESIGN {i}: {design.name}")
        print('=' * 80)
        print()
        print(f"Description: {design.description}")
        print()
        print(f"Providers: {', '.join(design.providers)}")
        print(f"Total Cost: ${design.total_monthly_cost:.2f}/month")
        print(f"Resources: {design.total_vcpus} vCPU, {design.total_ram_gb}GB RAM, {design.gpus} GPU(s)")
        print(f"Redundancy: Level {design.redundancy_level} (can survive {design.redundancy_level} node failure(s))")
        print(f"Geographic Distribution: {design.regions} region(s)")
        print(f"ABCFC Score: {design.abcfc_score:.1f}")
        print()
        print("Nodes:")
        for node in design.nodes:
            print(f"  • {node['provider']} ({node['region']})")
            print(f"    Specs: {node['specs']}")
            print(f"    Role: {node['role']}")
            print(f"    Cost: ${node['cost']:.2f}/month")
        print()

    print("=" * 80)
    print("📈 COMPARISON MATRIX")
    print("=" * 80)
    print()

    print(f"{'Design':<30} {'Cost':<12} {'ABCFC':<10} {'Redundancy':<12} {'Regions':<10}")
    print("-" * 80)
    for design in designs:
        print(f"{design.name:<30} ${design.total_monthly_cost:<11.2f} {design.abcfc_score:<10.1f} "
              f"Level {design.redundancy_level:<10} {design.regions:<10}")
    print()

    print("=" * 80)
    print("🎯 RECOMMENDATIONS BY USE CASE")
    print("=" * 80)
    print()

    print("IF BUDGET < $25/month:")
    print("  → Design 3: Geographic Redundancy (DO)")
    print("  → $20/month, good redundancy, no GPU")
    print()

    print("IF BUDGET $25-$100/month:")
    print("  → Design 5: Cost-Optimized Hybrid")
    print("  → $99.90/month, Hetzner + Oracle + occasional GPU")
    print("  → Best value for serious usage")
    print()

    print("IF BUDGET $100-$400/month:")
    print("  → Design 4: Hybrid Multi-Provider (OPTIMAL)")
    print("  → $391.80/month, full redundancy + regular GPU usage")
    print("  → Production-ready with ML capability")
    print()

    print("IF NO BUDGET CONSTRAINT:")
    print("  → Design 6: Maximum Performance")
    print("  → $1220/month, maximum power and redundancy")
    print("  → Enterprise-grade setup")
    print()

    print("=" * 80)
    print("💡 RECOMMENDED: Design 5 (Cost-Optimized Hybrid)")
    print("=" * 80)
    print()

    print("WHY:")
    print("  ✅ Hetzner dedicated: Better specs than DO at same price")
    print("  ✅ Oracle free tier: $0 backup node forever")
    print("  ✅ GPU on-demand: Only pay when needed")
    print("  ✅ Total: ~$100/month for production-ready setup")
    print("  ✅ Can scale GPU usage up/down dynamically")
    print()

    print("CURRENT STATE vs RECOMMENDED:")
    print("-" * 80)
    print(f"Current: 9 DO droplets, $72/month, 68 vCPU, 136GB RAM, no GPU")
    print(f"  • 8 nodes idle")
    print(f"  • Primary overloaded (108% CPU)")
    print(f"  • No geographic redundancy")
    print()
    print(f"Recommended: 3 nodes, $99.90/month, 12 vCPU, 88GB RAM, GPU available")
    print(f"  • All nodes utilized")
    print(f"  • Better specs per node (Hetzner: 64GB vs DO: 16GB)")
    print(f"  • Multi-region redundancy")
    print(f"  • GPU capability for ML/AI")
    print()

    print("=" * 80)
    print("📋 MIGRATION PLAN TO DESIGN 5")
    print("=" * 80)
    print()

    print("STEP 1: Provision Hetzner Dedicated Server (US)")
    print("  • Order AX41 from Hetzner (Ashburn)")
    print("  • 8 cores, 64GB RAM, 512GB NVMe")
    print("  • Setup time: 24 hours")
    print("  • Cost: $49.90/month")
    print()

    print("STEP 2: Migrate services from DO to Hetzner")
    print("  • Deploy hands-off-engine")
    print("  • Migrate all services")
    print("  • Test thoroughly")
    print("  • Time: 2-3 hours")
    print()

    print("STEP 3: Setup Oracle Cloud Free Tier")
    print("  • Create Oracle account")
    print("  • Provision ARM instance (4 CPU, 24GB)")
    print("  • Configure as backup node")
    print("  • Cost: $0 forever")
    print()

    print("STEP 4: Destroy all 9 DO droplets")
    print("  • Verify everything running on Hetzner")
    print("  • Destroy all DO droplets")
    print("  • Savings: $72/month")
    print()

    print("STEP 5: Setup GPU (when needed)")
    print("  • Create Vast.ai account")
    print("  • Add $50 balance")
    print("  • Spin up GPU when doing ML work")
    print("  • Cost: $0 when not used, ~$0.40/hr when used")
    print()

    print("=" * 80)
    print("💰 COST BREAKDOWN (Design 5)")
    print("=" * 80)
    print()

    print("FIXED COSTS:")
    print("  Hetzner AX41 (US):           $49.90/month")
    print("  Oracle Cloud Free:           $0.00/month")
    print("                               ────────────")
    print("  Base infrastructure:         $49.90/month")
    print()

    print("VARIABLE COSTS (GPU):")
    print("  Never use GPU:               +$0.00/month")
    print("  Occasional (1hr/day):        +$12.00/month")
    print("  Light usage (2hr/day):       +$24.00/month")
    print("  Medium usage (4hr/day):      +$50.00/month")
    print("  Heavy usage (8hr/day):       +$100.00/month")
    print()

    print("RECOMMENDED BUDGET:")
    print("  Base: $49.90 + GPU: $50 = $99.90/month")
    print("  (covers 4 hours/day GPU usage)")
    print()

    print("=" * 80)
    print("🎯 FINAL RECOMMENDATION")
    print("=" * 80)
    print()

    print("OPTIMAL INFRASTRUCTURE:")
    print("  1. Hetzner AX41 (Ashburn US) - $49.90/month")
    print("     • Primary node")
    print("     • 8 cores, 64GB RAM (4x better than DO!)")
    print("     • All trading + autonomous services")
    print()
    print("  2. Oracle Cloud ARM (Phoenix) - $0/month")
    print("     • Backup node")
    print("     • 4 cores, 24GB RAM")
    print("     • Geographic redundancy")
    print()
    print("  3. Vast.ai GPU (on-demand) - $0-100/month")
    print("     • ML/AI workloads")
    print("     • RTX 3090 or 4090")
    print("     • Only pay when running")
    print()

    print("TOTAL: ~$100/month for production-ready autonomous system")
    print()

    print("NEXT STEP: Provision Hetzner server and begin migration")
    print()

    # Save result
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_design": "Cost-Optimized Hybrid",
        "monthly_cost": 99.90,
        "nodes": [
            {
                "provider": "Hetzner",
                "type": "Dedicated AX41",
                "region": "Ashburn US",
                "specs": "8 CPU, 64GB RAM, 512GB NVMe",
                "role": "PRIMARY",
                "cost": 49.90
            },
            {
                "provider": "Oracle",
                "type": "ARM A1 (Always Free)",
                "region": "Phoenix",
                "specs": "4 CPU, 24GB RAM, 200GB storage",
                "role": "BACKUP",
                "cost": 0.0
            },
            {
                "provider": "Vast.ai",
                "type": "RTX 3090 (on-demand)",
                "region": "Flexible",
                "specs": "24GB VRAM",
                "role": "GPU",
                "cost": 50.0
            }
        ],
        "comparison": {
            "current_do": {
                "droplets": 9,
                "cost": 72.0,
                "vcpus": 68,
                "ram_gb": 136,
                "idle_nodes": 8,
                "gpu": 0
            },
            "recommended": {
                "nodes": 3,
                "cost": 99.90,
                "vcpus": 12,
                "ram_gb": 88,
                "idle_nodes": 0,
                "gpu": 1
            }
        },
        "next_steps": [
            "Order Hetzner AX41 dedicated server",
            "Setup Oracle Cloud free tier",
            "Migrate services from DO to Hetzner",
            "Destroy all 9 DO droplets",
            "Setup Vast.ai account for GPU"
        ]
    }

    output_file = Path("/root/hands-off-engine/analysis/clean_slate_infrastructure.json")
    output_file.write_text(json.dumps(result, indent=2))

    print(f"Full analysis saved to: {output_file}")
    print()


if __name__ == "__main__":
    analyze_requirements()
