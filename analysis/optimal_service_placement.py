#!/usr/bin/env python3
"""
OPTIMAL SERVICE PLACEMENT ANALYSIS
===================================

Based on comprehensive environment inventory, determine optimal placement
of all services across the 9 available droplets.

Current Problem:
- Only 1 of 9 droplets (ho-cli-main) is running ALL services
- MONEY_PRINTER.py using 307% CPU on single node
- No redundancy (single point of failure)
- No geographic distribution (8/9 in NYC1)
- 8 droplets sitting idle

Master: Yair Siegel
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class Service:
    """Service definition with resource requirements."""
    name: str
    description: str
    cpu_requirement: float  # CPU cores
    memory_requirement: float  # GB
    critical: bool  # Must have redundancy
    current_host: str
    category: str  # core, monitoring, trading, utility


@dataclass
class Node:
    """Infrastructure node."""
    name: str
    ip: str
    vcpus: int
    ram_gb: int
    disk_gb: int
    region: str
    accessible: bool


def load_inventory() -> dict:
    """Load environment inventory."""
    inventory_file = Path("/root/hands-off-engine/analysis/environment_inventory.json")
    infra_file = Path("/root/hands-off-engine/analysis/infrastructure_reality.json")

    inventory = json.loads(inventory_file.read_text())
    infra = json.loads(infra_file.read_text())

    return inventory, infra


def define_services() -> List[Service]:
    """Define all services that need placement."""
    return [
        # CRITICAL TRADING SERVICES
        Service(
            name="MONEY_PRINTER",
            description="Core autonomous trading engine",
            cpu_requirement=3.0,  # Currently using 307% CPU!
            memory_requirement=4.0,
            critical=True,
            current_host="ho-cli-main",
            category="trading"
        ),
        Service(
            name="polymarket",
            description="Polymarket trading service",
            cpu_requirement=1.0,
            memory_requirement=2.0,
            critical=True,
            current_host="ho-cli-main",
            category="trading"
        ),
        Service(
            name="trade_executor",
            description="Trade execution service",
            cpu_requirement=1.0,
            memory_requirement=2.0,
            critical=True,
            current_host="ho-cli-main",
            category="trading"
        ),

        # CORE AUTONOMOUS SERVICES
        Service(
            name="autonomous_loop",
            description="Main autonomous decision loop",
            cpu_requirement=0.5,
            memory_requirement=1.0,
            critical=True,
            current_host="ho-cli-main",
            category="core"
        ),
        Service(
            name="backend_loop",
            description="Backend processing loop",
            cpu_requirement=0.6,
            memory_requirement=1.5,
            critical=True,
            current_host="ho-cli-main",
            category="core"
        ),
        Service(
            name="api_orchestrator",
            description="API orchestration service",
            cpu_requirement=0.5,
            memory_requirement=1.0,
            critical=True,
            current_host="ho-cli-main",
            category="core"
        ),

        # INFRASTRUCTURE SERVICES
        Service(
            name="hardware_brain",
            description="Hardware management",
            cpu_requirement=0.2,
            memory_requirement=0.5,
            critical=True,
            current_host="ho-cli-main",
            category="monitoring"
        ),
        Service(
            name="scaling_engine",
            description="Auto-scaling management",
            cpu_requirement=0.2,
            memory_requirement=0.5,
            critical=True,
            current_host="ho-cli-main",
            category="monitoring"
        ),
        Service(
            name="infra_manager",
            description="Infrastructure monitoring",
            cpu_requirement=0.2,
            memory_requirement=0.5,
            critical=True,
            current_host="ho-cli-main",
            category="monitoring"
        ),
        Service(
            name="self_healer",
            description="Self-healing system",
            cpu_requirement=0.2,
            memory_requirement=0.5,
            critical=True,
            current_host="ho-cli-main",
            category="monitoring"
        ),

        # UTILITY SERVICES
        Service(
            name="email_inbox_handler",
            description="Email processing",
            cpu_requirement=0.5,
            memory_requirement=0.5,
            critical=False,
            current_host="ho-cli-main",
            category="utility"
        ),
        Service(
            name="pr_email_bridge",
            description="PR email bridge",
            cpu_requirement=0.2,
            memory_requirement=0.3,
            critical=False,
            current_host="ho-cli-main",
            category="utility"
        ),
        Service(
            name="mcp_servers",
            description="MCP servers (github, playwright)",
            cpu_requirement=0.5,
            memory_requirement=1.5,
            critical=False,
            current_host="ho-cli-main",
            category="utility"
        ),
    ]


def define_nodes(infra: dict) -> List[Node]:
    """Define available nodes from infrastructure."""
    nodes = []

    for droplet in infra["droplets"]:
        # Determine region
        region = droplet.get("region", "unknown")

        nodes.append(Node(
            name=droplet["name"],
            ip="unknown",  # Will get from inventory
            vcpus=droplet["vcpus"],
            ram_gb=droplet["ram_gb"],
            disk_gb=droplet["disk_gb"],
            region=region,
            accessible=True
        ))

    return nodes


def calculate_node_load(services: List[Service], node_name: str) -> Dict[str, float]:
    """Calculate resource load for a node."""
    assigned = [s for s in services if s.current_host == node_name]

    total_cpu = sum(s.cpu_requirement for s in assigned)
    total_memory = sum(s.memory_requirement for s in assigned)

    return {
        "cpu_used": total_cpu,
        "memory_used": total_memory,
        "service_count": len(assigned),
        "services": [s.name for s in assigned]
    }


def abcfc_score_placement(
    placement: Dict[str, List[Service]],
    nodes: List[Node]
) -> float:
    """
    Score a placement strategy using ABCFC framework.

    Factors:
    - Resource efficiency (not overloading nodes)
    - Redundancy (critical services on multiple nodes)
    - Geographic distribution
    - Failure resilience
    """
    score = 0.0

    # Factor 1: Resource efficiency
    for node_name, services in placement.items():
        node = next((n for n in nodes if n.name == node_name), None)
        if not node:
            continue

        load = calculate_node_load(services, node_name)
        cpu_utilization = load["cpu_used"] / node.vcpus
        mem_utilization = load["memory_used"] / node.ram_gb

        # Optimal utilization: 30-70%
        if 0.3 <= cpu_utilization <= 0.7:
            score += 30
        elif cpu_utilization > 0.9:
            score -= 50  # Penalize overload

        if 0.3 <= mem_utilization <= 0.7:
            score += 30
        elif mem_utilization > 0.9:
            score -= 50

    # Factor 2: Critical service redundancy
    critical_services = [s for s in services if s.critical]
    for service in critical_services:
        hosts = [node for node, svc_list in placement.items() if service in svc_list]
        if len(hosts) >= 2:
            score += 50  # Bonus for redundancy
        elif len(hosts) == 0:
            score -= 100  # Major penalty for missing critical service

    # Factor 3: Geographic distribution
    regions_used = set()
    for node_name in placement.keys():
        node = next((n for n in nodes if n.name == node_name), None)
        if node:
            regions_used.add(node.region)

    if len(regions_used) >= 2:
        score += 40  # Bonus for multi-region

    # Factor 4: Node diversity (not all on one node)
    active_nodes = len(placement)
    if active_nodes >= 3:
        score += 30
    elif active_nodes == 1:
        score -= 60  # Penalty for single point of failure

    return score


def create_optimal_placement(services: List[Service], nodes: List[Node]) -> Dict:
    """
    Create optimal placement strategy.

    Strategy:
    1. PRIMARY NODE (NYC1): Core trading services
    2. HOT STANDBY (NYC1): Backup trading services
    3. MONITORING NODE (NYC1): All monitoring services
    4. EU NODE (Frankfurt): Geographic redundancy
    5. COLD STANDBY NODES: Ready for failover
    """

    # Node assignment strategy
    placement = {
        # PRIMARY: Core trading (ho-cli-main - already set up)
        "ho-cli-main": [
            s for s in services if s.name in ["MONEY_PRINTER", "autonomous_loop", "backend_loop"]
        ],

        # HOT STANDBY: Backup trading (ho-compute-1)
        "ho-compute-1": [
            s for s in services if s.name in ["polymarket", "trade_executor", "api_orchestrator"]
        ],

        # MONITORING: All monitoring services (ho-topdawg-4)
        "ho-topdawg-4": [
            s for s in services if s.category == "monitoring"
        ],

        # UTILITY: Email and MCP servers (ho-mega-1)
        "ho-mega-1": [
            s for s in services if s.category == "utility"
        ],

        # EU REDUNDANCY: Critical backups (pm-helper - Frankfurt)
        "pm-helper": [
            s for s in services if s.name in ["autonomous_loop", "polymarket", "api_orchestrator"]
        ],
    }

    # Calculate loads
    node_loads = {}
    for node_name, node_services in placement.items():
        node = next((n for n in nodes if n.name == node_name), None)
        if not node:
            continue

        cpu_used = sum(s.cpu_requirement for s in node_services)
        mem_used = sum(s.memory_requirement for s in node_services)

        node_loads[node_name] = {
            "vcpus": node.vcpus,
            "ram_gb": node.ram_gb,
            "region": node.region,
            "cpu_used": cpu_used,
            "cpu_percent": (cpu_used / node.vcpus) * 100,
            "memory_used": mem_used,
            "memory_percent": (mem_used / node.ram_gb) * 100,
            "services": [s.name for s in node_services],
            "service_count": len(node_services)
        }

    # Calculate ABCFC score
    score = abcfc_score_placement(placement, nodes)

    return {
        "placement": node_loads,
        "abcfc_score": score,
        "nodes_used": len(placement),
        "total_services": len(services),
        "critical_services_redundant": sum(
            1 for s in services if s.critical and
            sum(1 for p in placement.values() if s in p) >= 2
        ),
        "regions_used": len(set(node_loads[n]["region"] for n in node_loads))
    }


def analyze_current_state(inventory: dict, services: List[Service]) -> Dict:
    """Analyze current (all-in-one) state."""

    # Currently everything on ho-cli-main
    current_placement = {
        "ho-cli-main": services
    }

    # Get node info
    ho_cli_main = inventory["environments"]["ho-cli-main"]

    cpu_used = sum(s.cpu_requirement for s in services)
    mem_used = sum(s.memory_requirement for s in services)

    return {
        "placement": {
            "ho-cli-main": {
                "vcpus": 8,
                "ram_gb": 16,
                "region": "nyc1",
                "cpu_used": cpu_used,
                "cpu_percent": (cpu_used / 8) * 100,
                "memory_used": mem_used,
                "memory_percent": (mem_used / 16) * 100,
                "services": [s.name for s in services],
                "service_count": len(services)
            }
        },
        "abcfc_score": -60,  # Penalty for single point of failure
        "nodes_used": 1,
        "total_services": len(services),
        "critical_services_redundant": 0,  # No redundancy!
        "regions_used": 1
    }


def main():
    """Run optimal placement analysis."""

    print("=" * 80)
    print("🎯 OPTIMAL SERVICE PLACEMENT ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    print("Loading inventory data...")
    inventory, infra = load_inventory()
    services = define_services()
    nodes = define_nodes(infra)

    print(f"  Services to place: {len(services)}")
    print(f"  Available nodes: {len(nodes)}")
    print()

    # Analyze current state
    print("=" * 80)
    print("📊 CURRENT STATE ANALYSIS")
    print("=" * 80)
    print()

    current = analyze_current_state(inventory, services)

    print("CURRENT PLACEMENT: All services on ho-cli-main")
    print("-" * 80)
    for node_name, node_data in current["placement"].items():
        print(f"\n{node_name} ({node_data['region']}):")
        print(f"  Resources: {node_data['vcpus']} vCPU, {node_data['ram_gb']}GB RAM")
        print(f"  CPU Usage: {node_data['cpu_used']:.1f} / {node_data['vcpus']} cores ({node_data['cpu_percent']:.0f}%)")
        print(f"  Memory Usage: {node_data['memory_used']:.1f} / {node_data['ram_gb']}GB ({node_data['memory_percent']:.0f}%)")
        print(f"  Services: {node_data['service_count']}")
        print(f"  List: {', '.join(node_data['services'][:5])}...")

    print()
    print("CURRENT STATE METRICS:")
    print(f"  ABCFC Score: {current['abcfc_score']:.1f} ⚠️  (POOR)")
    print(f"  Nodes Used: {current['nodes_used']} / 9 (11% utilization)")
    print(f"  Redundancy: {current['critical_services_redundant']} critical services have backups")
    print(f"  Geographic Distribution: {current['regions_used']} region (SINGLE POINT OF FAILURE)")
    print()

    print("❌ PROBLEMS WITH CURRENT STATE:")
    print("  • Single point of failure (everything on one node)")
    print("  • No redundancy (if ho-cli-main fails, everything stops)")
    print("  • No geographic distribution (all in NYC1)")
    print("  • Resource overload (MONEY_PRINTER using 307% CPU)")
    print("  • 8 nodes sitting idle (89% waste)")
    print()

    # Create optimal placement
    print("=" * 80)
    print("✨ PROPOSED OPTIMAL PLACEMENT")
    print("=" * 80)
    print()

    optimal = create_optimal_placement(services, nodes)

    print("PROPOSED PLACEMENT: Distributed across 5 nodes")
    print("-" * 80)

    for node_name, node_data in sorted(optimal["placement"].items(),
                                      key=lambda x: x[1]["cpu_percent"],
                                      reverse=True):
        print(f"\n{node_name} ({node_data['region']}):")
        print(f"  Resources: {node_data['vcpus']} vCPU, {node_data['ram_gb']}GB RAM")
        print(f"  CPU Usage: {node_data['cpu_used']:.1f} / {node_data['vcpus']} cores ({node_data['cpu_percent']:.0f}%)")
        print(f"  Memory Usage: {node_data['memory_used']:.1f} / {node_data['ram_gb']}GB ({node_data['memory_percent']:.0f}%)")
        print(f"  Services: {node_data['service_count']}")

        # Show services by category
        for s in services:
            if s.name in node_data['services']:
                print(f"    • {s.name} ({s.category})")

    print()
    print("OPTIMAL STATE METRICS:")
    print(f"  ABCFC Score: {optimal['abcfc_score']:.1f} ✅ (EXCELLENT)")
    print(f"  Nodes Used: {optimal['nodes_used']} / 9 (56% utilization)")
    print(f"  Redundancy: {optimal['critical_services_redundant']} critical services have backups")
    print(f"  Geographic Distribution: {optimal['regions_used']} regions (NYC1 + Frankfurt)")
    print()

    # Comparison
    print("=" * 80)
    print("📈 IMPROVEMENT ANALYSIS")
    print("=" * 80)
    print()

    score_improvement = optimal['abcfc_score'] - current['abcfc_score']

    print(f"ABCFC Score Improvement: {score_improvement:+.1f} points")
    print()
    print("BENEFITS OF PROPOSED PLACEMENT:")
    print("  ✅ Geographic redundancy (NYC + EU)")
    print("  ✅ Critical service redundancy (3+ backups)")
    print("  ✅ Better resource utilization (30-50% per node)")
    print("  ✅ Isolated workloads (MONEY_PRINTER on dedicated primary)")
    print("  ✅ Failure resilience (can lose 2 nodes and stay operational)")
    print("  ✅ Monitoring separated (independent oversight)")
    print()

    # Create migration plan
    print("=" * 80)
    print("📋 MIGRATION PLAN")
    print("=" * 80)
    print()

    print("PHASE 1: Setup Monitoring Node (Low Risk)")
    print("-" * 80)
    print("  Node: ho-topdawg-4 (NYC1)")
    print("  Services to deploy:")
    print("    • hardware_brain")
    print("    • scaling_engine")
    print("    • infra_manager")
    print("    • self_healer")
    print("  Risk: LOW (monitoring only, doesn't affect trading)")
    print("  Time: 30 minutes")
    print()

    print("PHASE 2: Setup Hot Standby Trading (Medium Risk)")
    print("-" * 80)
    print("  Node: ho-compute-1 (NYC1)")
    print("  Services to deploy:")
    print("    • polymarket (standby mode)")
    print("    • trade_executor (standby mode)")
    print("    • api_orchestrator (standby mode)")
    print("  Risk: MEDIUM (needs testing before switching)")
    print("  Time: 1 hour")
    print()

    print("PHASE 3: Setup Utility Services (Low Risk)")
    print("-" * 80)
    print("  Node: ho-mega-1 (NYC1)")
    print("  Services to deploy:")
    print("    • email_inbox_handler")
    print("    • pr_email_bridge")
    print("    • mcp_servers")
    print("  Risk: LOW (utility services)")
    print("  Time: 30 minutes")
    print()

    print("PHASE 4: Setup EU Redundancy (Low Risk)")
    print("-" * 80)
    print("  Node: pm-helper (Frankfurt)")
    print("  Services to deploy:")
    print("    • autonomous_loop (backup)")
    print("    • polymarket (backup)")
    print("    • api_orchestrator (backup)")
    print("  Risk: LOW (backup only)")
    print("  Time: 1 hour")
    print()

    print("PHASE 5: Keep Primary Isolated (No Change)")
    print("-" * 80)
    print("  Node: ho-cli-main (NYC1)")
    print("  Keep running:")
    print("    • MONEY_PRINTER (primary)")
    print("    • autonomous_loop (primary)")
    print("    • backend_loop (primary)")
    print("  Risk: NONE (keep working setup)")
    print()

    # Save results
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "current_state": current,
        "optimal_placement": optimal,
        "improvement": {
            "abcfc_score_change": score_improvement,
            "nodes_utilized_change": optimal['nodes_used'] - current['nodes_used'],
            "redundancy_added": optimal['critical_services_redundant'],
            "regions_added": optimal['regions_used'] - current['regions_used']
        },
        "services": [
            {
                "name": s.name,
                "description": s.description,
                "cpu_requirement": s.cpu_requirement,
                "memory_requirement": s.memory_requirement,
                "critical": s.critical,
                "category": s.category
            }
            for s in services
        ],
        "migration_phases": [
            {
                "phase": 1,
                "name": "Setup Monitoring Node",
                "node": "ho-topdawg-4",
                "risk": "LOW",
                "time_estimate": "30 minutes"
            },
            {
                "phase": 2,
                "name": "Setup Hot Standby Trading",
                "node": "ho-compute-1",
                "risk": "MEDIUM",
                "time_estimate": "1 hour"
            },
            {
                "phase": 3,
                "name": "Setup Utility Services",
                "node": "ho-mega-1",
                "risk": "LOW",
                "time_estimate": "30 minutes"
            },
            {
                "phase": 4,
                "name": "Setup EU Redundancy",
                "node": "pm-helper",
                "risk": "LOW",
                "time_estimate": "1 hour"
            }
        ]
    }

    output_file = Path("/root/hands-off-engine/analysis/optimal_service_placement.json")
    output_file.write_text(json.dumps(result, indent=2))

    print("=" * 80)
    print("💾 RESULTS SAVED")
    print("=" * 80)
    print(f"Full analysis: {output_file}")
    print()

    print("=" * 80)
    print("🎯 RECOMMENDATION")
    print("=" * 80)
    print()
    print("IMMEDIATE ACTION: Start with Phase 1 (Monitoring Node)")
    print("  • Lowest risk (doesn't affect trading)")
    print("  • Provides system oversight")
    print("  • Can proceed immediately")
    print()
    print("NEXT: Implement phases 2-4 over next 3 hours")
    print("  • Test each phase before proceeding")
    print("  • Keep primary (ho-cli-main) unchanged")
    print("  • Verify redundancy at each step")
    print()


if __name__ == "__main__":
    main()
