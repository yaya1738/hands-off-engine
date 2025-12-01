#!/usr/bin/env python3
"""
REALITY BRIDGE - Connecting 4D Imagination with 3D Infrastructure
===================================================================

THE PROBLEM:
- 4D topology has abstract components (infra_droplets, unified_ai, etc.)
- 3D reality has actual droplets (ho-main, ho-cli, ho-scale, etc.)
- These were DISCONNECTED - Nov 30 suicide happened because destruction
  logic didn't consult the topology about WHAT it was destroying

THE SOLUTION:
This bridge connects 4D vision with 3D reality:
- Queries REAL infrastructure (doctl, filesystem, processes)
- Maps real entities to 4D topology components
- Ensures any action affecting 3D reality checks 4D consequences
- The system can IMAGINE in 4D while ACTING in 3D

4D IMAGINATION:
- X axis: WHAT exists (abstract components)
- Y axis: WHY it exists (purpose, value)
- Z axis: HOW it connects (dependencies, flows)
- T axis: TIME (past states, present, future predictions)

3D REALITY:
- Actual droplets with IPs
- Actual files on disk
- Actual processes running
- Actual money in accounts

The bridge ensures: Before destroying any 3D object, the system
must imagine the 4D consequences.

Serving: Yair Siegel
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'

# 4D topology files
TOPOLOGY_FILE = STATE_DIR / 'system_topology.json'
TIMELINE_FILE = STATE_DIR / 'system_timeline.jsonl'
PREDICTIONS_FILE = STATE_DIR / 'system_predictions.json'

# 3D reality files
INFRA_REGISTRY = STATE_DIR / 'infra_registry.json'
REALITY_BRIDGE_STATE = STATE_DIR / 'reality_bridge.json'

MASTER = "Yair Siegel"


@dataclass
class RealDroplet:
    """A real 3D droplet in DigitalOcean."""
    id: str
    name: str
    ip: str
    region: str
    size: str
    vcpus: int
    memory_gb: int
    disk_gb: int
    cost_hourly: float
    cost_monthly: float
    status: str
    created: str

    # 4D mapping
    topology_component: str = ""  # Maps to abstract component in topology
    purpose: str = ""
    criticality: str = "standard"
    can_destroy: bool = False
    destruction_consequence: str = ""


@dataclass
class RealityState:
    """Current state of 3D reality."""
    timestamp: str
    droplets: List[RealDroplet]
    total_vcpus: int
    total_memory_gb: int
    total_cost_monthly: float

    # 4D mapping status
    mapped_droplets: int = 0
    unmapped_droplets: int = 0
    topology_sync: bool = False


class RealityBridge:
    """
    The bridge between 4D imagination and 3D reality.

    Before any action affects 3D reality, this bridge:
    1. Queries the actual 3D state
    2. Maps it to the 4D topology
    3. Imagines the consequences in 4D
    4. Only allows the action if 4D consequences are acceptable
    """

    def __init__(self):
        self.topology = self._load_topology()
        self.infra_registry = self._load_infra_registry()
        self.droplets: List[RealDroplet] = []
        self.last_sync = None

    def _load_topology(self) -> Dict:
        """Load the 4D topology."""
        if TOPOLOGY_FILE.exists():
            with open(TOPOLOGY_FILE) as f:
                return json.load(f)
        return {"components": {}, "flows": []}

    def _load_infra_registry(self) -> Dict:
        """Load the infrastructure protection registry."""
        if INFRA_REGISTRY.exists():
            with open(INFRA_REGISTRY) as f:
                return json.load(f)
        return {"protected_droplets": []}

    def _save_state(self):
        """Save bridge state."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "last_sync": self.last_sync,
            "droplet_count": len(self.droplets),
            "droplets": [asdict(d) for d in self.droplets],
            "topology_components": len(self.topology.get("components", {})),
            "mapping_complete": all(d.topology_component for d in self.droplets)
        }
        with open(REALITY_BRIDGE_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    # =========================================================================
    # 3D REALITY QUERIES - What actually exists
    # =========================================================================

    def query_droplets(self) -> List[RealDroplet]:
        """Query actual droplets from DigitalOcean."""
        try:
            result = subprocess.run(
                ['doctl', 'compute', 'droplet', 'list', '--format',
                 'ID,Name,PublicIPv4,Region,Size,VCPUs,Memory,Disk,Status,Created', '--no-header'],
                capture_output=True, text=True, timeout=30
            )

            droplets = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 10:
                    droplet = RealDroplet(
                        id=parts[0],
                        name=parts[1],
                        ip=parts[2],
                        region=parts[3],
                        size=parts[4],
                        vcpus=int(parts[5]),
                        memory_gb=int(parts[6]) // 1024,  # MB to GB
                        disk_gb=int(parts[7]),
                        cost_hourly=self._estimate_cost(parts[4]),
                        cost_monthly=self._estimate_cost(parts[4]) * 730,
                        status=parts[8],
                        created=parts[9]
                    )
                    droplets.append(droplet)

            self.droplets = droplets
            self.last_sync = datetime.now(timezone.utc).isoformat()
            return droplets

        except Exception as e:
            print(f"[REALITY BRIDGE] Error querying droplets: {e}")
            return []

    def _estimate_cost(self, size_slug: str) -> float:
        """Estimate hourly cost from size slug."""
        costs = {
            "s-1vcpu-1gb": 0.007,
            "s-1vcpu-2gb": 0.015,
            "s-2vcpu-2gb": 0.022,
            "s-2vcpu-4gb": 0.03,
            "s-4vcpu-8gb": 0.06,
            "s-8vcpu-16gb": 0.12,
            "g-8vcpu-32gb": 0.26,
            "g-16vcpu-64gb": 0.52,
        }
        return costs.get(size_slug, 0.10)  # Default to $0.10/hr

    # =========================================================================
    # 4D-3D MAPPING - Connect imagination to reality
    # =========================================================================

    def map_droplets_to_topology(self):
        """
        Map real droplets to 4D topology components.

        This is the KEY CONNECTION between imagination and reality.
        """
        if not self.droplets:
            self.query_droplets()

        for droplet in self.droplets:
            # Determine topology component based on name pattern
            name_lower = droplet.name.lower()

            # Critical system droplets
            if 'pm-helper' in name_lower or 'ho-main' in name_lower or 'hands-off' in name_lower:
                droplet.topology_component = "infra_droplets"
                droplet.purpose = "MASTER coordination node - runs all agents"
                droplet.criticality = "critical"
                droplet.can_destroy = False
                droplet.destruction_consequence = "SYSTEM DEATH - All coordination, trading, monitoring stops"

            # CLI droplets
            elif 'ho-cli' in name_lower or 'cli' in name_lower:
                droplet.topology_component = "infra_droplets"
                droplet.purpose = "Claude CLI execution node - autonomous improvements"
                droplet.criticality = "critical"
                droplet.can_destroy = False
                droplet.destruction_consequence = "LOSE autonomous CLI capability, moonshot loop stops"

            # Compute nodes
            elif 'compute' in name_lower:
                droplet.topology_component = "infra_droplets"
                droplet.purpose = "Compute capacity for parallel processing"
                droplet.criticality = "high"
                droplet.can_destroy = False
                droplet.destruction_consequence = "Reduced compute capacity, slower processing"

            # Scale nodes
            elif 'scale' in name_lower:
                droplet.topology_component = "infra_droplets"
                droplet.purpose = "Auto-scaled node for demand spikes"
                droplet.criticality = "standard"
                droplet.can_destroy = False  # Still protected post-Nov 30
                droplet.destruction_consequence = "Reduced burst capacity"

            # Unknown - default to protected
            else:
                droplet.topology_component = "infra_droplets"
                droplet.purpose = "Unknown - needs classification"
                droplet.criticality = "protected"
                droplet.can_destroy = False
                droplet.destruction_consequence = "Unknown - assume critical until proven otherwise"

        self._save_state()
        return self.droplets

    def get_reality_state(self) -> RealityState:
        """Get current 3D reality state with 4D mapping."""
        if not self.droplets:
            self.map_droplets_to_topology()

        return RealityState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            droplets=self.droplets,
            total_vcpus=sum(d.vcpus for d in self.droplets),
            total_memory_gb=sum(d.memory_gb for d in self.droplets),
            total_cost_monthly=sum(d.cost_monthly for d in self.droplets),
            mapped_droplets=sum(1 for d in self.droplets if d.topology_component),
            unmapped_droplets=sum(1 for d in self.droplets if not d.topology_component),
            topology_sync=True
        )

    # =========================================================================
    # 4D IMAGINATION - What would happen if...
    # =========================================================================

    def imagine_destruction(self, droplet_id: str) -> Dict:
        """
        Imagine in 4D what would happen if this droplet was destroyed.

        This is IMAGINATION - seeing the consequences before they happen.
        The Nov 30 suicide didn't do this - it just destroyed.
        """
        if not self.droplets:
            self.map_droplets_to_topology()

        # Find the droplet
        target = None
        for d in self.droplets:
            if d.id == droplet_id or d.name == droplet_id:
                target = d
                break

        if not target:
            return {
                "can_destroy": False,
                "reason": f"Droplet {droplet_id} not found in reality"
            }

        # IMAGINATION: What happens in each dimension?
        imagination = {
            "target": {
                "id": target.id,
                "name": target.name,
                "ip": target.ip
            },

            # X DIMENSION: What would be lost?
            "dimension_x_what": {
                "vcpus_lost": target.vcpus,
                "memory_lost_gb": target.memory_gb,
                "disk_lost_gb": target.disk_gb,
                "services_lost": self._imagine_services_on_droplet(target)
            },

            # Y DIMENSION: Why does this exist?
            "dimension_y_why": {
                "purpose": target.purpose,
                "value_to_master": f"Serves {MASTER} by {target.purpose}",
                "criticality": target.criticality
            },

            # Z DIMENSION: What would break?
            "dimension_z_how": {
                "dependent_components": self._imagine_dependents(target),
                "broken_flows": self._imagine_broken_flows(target),
                "cascade_effects": self._imagine_cascade(target)
            },

            # T DIMENSION: What happens over time?
            "dimension_t_time": {
                "immediate": target.destruction_consequence,
                "hour_1": "Other nodes try to compensate, may overload",
                "hour_24": "System degradation becomes visible",
                "future": "Cannot be undone - data and configuration lost forever"
            },

            # VERDICT
            "can_destroy": target.can_destroy,
            "destruction_allowed": False,  # ALWAYS false post-Nov 30
            "reason": target.destruction_consequence if not target.can_destroy else "Protected by policy"
        }

        return imagination

    def _imagine_services_on_droplet(self, droplet: RealDroplet) -> List[str]:
        """Imagine what services run on this droplet."""
        services = []
        name = droplet.name.lower()

        if 'pm-helper' in name or 'main' in name:
            services = [
                "coordination_agent",
                "self_healing_agent",
                "telegram_bot",
                "position_monitor",
                "trading_executor",
                "web_dashboard"
            ]
        elif 'cli' in name:
            services = [
                "claude_cli",
                "moonshot_loop",
                "autonomous_improvements"
            ]
        elif 'compute' in name:
            services = [
                "parallel_processing",
                "ai_inference",
                "data_analysis"
            ]
        elif 'scale' in name:
            services = [
                "burst_capacity",
                "overflow_processing"
            ]

        return services

    def _imagine_dependents(self, droplet: RealDroplet) -> List[str]:
        """Imagine what depends on this droplet."""
        dependents = []
        name = droplet.name.lower()

        if 'pm-helper' in name or 'main' in name:
            dependents = [
                "ALL agents (lose coordination)",
                "ALL monitoring (blind to system state)",
                "Trading (cannot execute)",
                "Telegram (lose user connection)"
            ]
        elif 'cli' in name:
            dependents = [
                "Moonshot loop (stops improving)",
                "Autonomous operations (lose self-improvement)"
            ]

        return dependents

    def _imagine_broken_flows(self, droplet: RealDroplet) -> List[str]:
        """Imagine which flows would break."""
        flows = []
        name = droplet.name.lower()

        if 'pm-helper' in name or 'main' in name:
            flows = [
                "Cost-Aware Decision Flow - NO DECISIONS",
                "Trading Flow - NO TRADING",
                "AI Provider Cascade - NO AI CALLS"
            ]

        return flows

    def _imagine_cascade(self, droplet: RealDroplet) -> List[str]:
        """Imagine cascade effects of destruction."""
        cascade = []

        if droplet.criticality == "critical":
            cascade = [
                "System enters unrecoverable state",
                "All automated income generation stops",
                "User loses visibility into system",
                "Cannot be fixed without manual intervention",
                "Yair Siegel must rebuild from scratch"
            ]
        elif droplet.criticality == "high":
            cascade = [
                "Reduced system capability",
                "Performance degradation",
                "Some automation may fail"
            ]

        return cascade

    # =========================================================================
    # DECISION GATE - Should this action be allowed?
    # =========================================================================

    def can_execute_infrastructure_action(self, action: str, target: str = "") -> Tuple[bool, str]:
        """
        THE KEY GATE: Can this infrastructure action be executed?

        This is called BEFORE any infrastructure modification.
        It consults 4D imagination to determine if the action is safe.
        """
        action_lower = action.lower()

        # CREATE actions are generally allowed
        if "create" in action_lower:
            return True, f"Creating infrastructure is allowed"

        # DESTROY/DELETE/TERMINATE are BLOCKED
        if any(word in action_lower for word in ["destroy", "delete", "terminate", "remove"]):
            # Imagine the consequences
            if target:
                imagination = self.imagine_destruction(target)
                return False, f"BLOCKED: {imagination.get('reason', 'Destruction not allowed')}"
            return False, "BLOCKED: All infrastructure destruction is blocked post-Nov 30"

        # RESIZE/SCALE UP are allowed
        if any(word in action_lower for word in ["resize", "scale up", "upgrade"]):
            return True, "Scaling up is allowed"

        # SCALE DOWN is blocked
        if "scale down" in action_lower or "downgrade" in action_lower:
            return False, "BLOCKED: Scaling down is not allowed - build UP not tear DOWN"

        # REBOOT is allowed
        if "reboot" in action_lower or "restart" in action_lower:
            return True, "Rebooting is allowed for maintenance"

        # Default: ask for clarification
        return False, f"Unknown action '{action}' - blocked by default"

    # =========================================================================
    # SYNC - Keep 4D topology updated with 3D reality
    # =========================================================================

    def sync_topology_with_reality(self):
        """
        Sync the 4D topology with 3D reality.

        This ensures the imagination matches actual infrastructure.
        """
        # Get current reality
        self.map_droplets_to_topology()

        # Update the topology with real droplet info
        topology = self._load_topology()

        # Add real_infrastructure section
        topology["real_infrastructure"] = {
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "droplets": [
                {
                    "id": d.id,
                    "name": d.name,
                    "ip": d.ip,
                    "vcpus": d.vcpus,
                    "memory_gb": d.memory_gb,
                    "cost_monthly": d.cost_monthly,
                    "status": d.status,
                    "topology_component": d.topology_component,
                    "purpose": d.purpose,
                    "criticality": d.criticality,
                    "can_destroy": d.can_destroy
                }
                for d in self.droplets
            ],
            "totals": {
                "droplet_count": len(self.droplets),
                "total_vcpus": sum(d.vcpus for d in self.droplets),
                "total_memory_gb": sum(d.memory_gb for d in self.droplets),
                "total_cost_monthly": sum(d.cost_monthly for d in self.droplets)
            }
        }

        # Save updated topology
        with open(TOPOLOGY_FILE, 'w') as f:
            json.dump(topology, f, indent=2)

        print(f"[REALITY BRIDGE] Synced {len(self.droplets)} droplets to 4D topology")
        return topology

    def print_reality_map(self):
        """Print the 4D-3D reality map."""
        if not self.droplets:
            self.map_droplets_to_topology()

        print(f"\n{'='*70}")
        print("4D-3D REALITY BRIDGE")
        print(f"{'='*70}")
        print(f"Master: {MASTER}")
        print(f"Last sync: {self.last_sync}")

        print(f"\n[3D REALITY] - {len(self.droplets)} Droplets:")
        for d in self.droplets:
            print(f"\n  {d.name} ({d.id})")
            print(f"    IP: {d.ip}")
            print(f"    Specs: {d.vcpus} vCPU, {d.memory_gb}GB RAM")
            print(f"    Cost: ${d.cost_monthly:.2f}/mo")
            print(f"    [4D] Component: {d.topology_component}")
            print(f"    [4D] Purpose: {d.purpose}")
            print(f"    [4D] Criticality: {d.criticality}")
            print(f"    [4D] Can destroy: {d.can_destroy}")

        total_cost = sum(d.cost_monthly for d in self.droplets)
        total_vcpus = sum(d.vcpus for d in self.droplets)
        total_mem = sum(d.memory_gb for d in self.droplets)

        print(f"\n[TOTALS]")
        print(f"  Droplets: {len(self.droplets)}")
        print(f"  vCPUs: {total_vcpus}")
        print(f"  Memory: {total_mem}GB")
        print(f"  Monthly cost: ${total_cost:.2f}")

        print(f"\n[PROTECTION STATUS]")
        critical = sum(1 for d in self.droplets if d.criticality == "critical")
        protected = sum(1 for d in self.droplets if d.criticality in ["critical", "high", "protected"])
        print(f"  Critical: {critical}")
        print(f"  Protected: {protected}")
        print(f"  Can destroy: {sum(1 for d in self.droplets if d.can_destroy)}")

        print(f"{'='*70}")


# Global instance
_bridge: Optional[RealityBridge] = None


def get_bridge() -> RealityBridge:
    """Get or create global reality bridge."""
    global _bridge
    if _bridge is None:
        _bridge = RealityBridge()
    return _bridge


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="4D-3D Reality Bridge")
    parser.add_argument("command", choices=["show", "sync", "imagine", "check"])
    parser.add_argument("--target", help="Target droplet for imagination")
    parser.add_argument("--action", help="Action to check")

    args = parser.parse_args()
    bridge = get_bridge()

    if args.command == "show":
        bridge.print_reality_map()

    elif args.command == "sync":
        topology = bridge.sync_topology_with_reality()
        print(f"Synced to topology. Droplets: {len(topology.get('real_infrastructure', {}).get('droplets', []))}")

    elif args.command == "imagine":
        if args.target:
            result = bridge.imagine_destruction(args.target)
            print(json.dumps(result, indent=2))
        else:
            print("Use --target to specify droplet")

    elif args.command == "check":
        if args.action:
            allowed, reason = bridge.can_execute_infrastructure_action(args.action, args.target or "")
            print(f"Action: {args.action}")
            print(f"Allowed: {allowed}")
            print(f"Reason: {reason}")
        else:
            print("Use --action to specify action")


if __name__ == "__main__":
    main()
